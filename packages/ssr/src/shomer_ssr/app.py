# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""The Shomer frontend server.

It renders one Jinja shell and hands the browser the config it needs:

* ``GET /healthz`` — liveness probe.
* ``GET /favicon.ico`` — the branding icon, served before the catch-all.
* ``GET /{path}`` — the app shell, for every client route.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import Response
from starlette.types import Scope
from tripack_container import Container, Inject
from tripack_container.fastapi import TripackAPI

from shomer_lib.contracts import Settings
from shomer_lib.module import build_container

from . import __version__

# Both directories are populated by `packages/web` at build time — never
# edit them directly; edit the upstream sources and run
# `npm run build --workspace packages/web`.
TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"

# Generated from assets/shomer.svg by scripts/regen-icons.sh, and committed
# like the rest of static/ — the wheel ships whatever is on disk at build
# time, so a favicon that only exists after someone runs a script is a
# favicon missing from the release.
FAVICON = STATIC_DIR / "favicon.ico"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def frontend_config(settings: Settings) -> dict[str, str]:
    """Runtime config handed to the browser.

    Serialised into a ``<script id="app-config">`` tag by the template
    (``{{ config | tojson }}``) and read at mount time by
    ``packages/web/src/config.ts``. The server stays the single source of
    truth — nothing here is duplicated in the JS bundle.

    The issuer comes from the injected settings rather than from a
    constant here: the browser has to send the user to the same origin
    the tokens will claim to come from, and two copies of that value
    drift the first time one deployment is reconfigured.
    """
    return {
        "appName": "Shomer",
        "version": __version__,
        "issuer": settings.issuer,
    }


class DevAwareStaticFiles(StaticFiles):
    """``StaticFiles`` that advertises a sibling ``.map`` via the
    ``SourceMap`` response header when one exists on disk.

    Using the header rather than the conventional ``//# sourceMappingURL=``
    trailing comment keeps main.js / main.css byte-identical between dev
    and release, so a stray dev rebuild cannot slip a dev-only marker into
    a release commit. The watch build writes ``main.js.map`` next to
    ``main.js`` without appending the comment; release builds write no map
    at all, so this branch silently no-ops in production.

    Chrome, Firefox and Safari devtools treat the ``SourceMap`` response
    header as equivalent to the in-bundle comment.
    """

    async def get_response(self, path: str, scope: Scope) -> Response:
        response = await super().get_response(path, scope)
        # `self.directory` is typed `str | PathLike[str] | None` on the
        # parent because StaticFiles also supports the `packages=`
        # initialiser; the constructor below always passes a real
        # directory, so the None branch is unreachable in practice but
        # kept to satisfy --strict mypy.
        if (
            response.status_code == 200
            and path.endswith((".js", ".css"))
            and self.directory is not None
        ):
            map_path = Path(self.directory) / f"{path}.map"
            if map_path.is_file():
                response.headers["SourceMap"] = f"/static/{path}.map"
        return response


def container_factory() -> Container:
    """Build the container the app runs on.

    A named function rather than a lambda so a test can substitute its
    own factory, and so a wiring failure at startup names something
    findable in the traceback.
    """
    return build_container()


app = TripackAPI(
    title="Shomer SSR",
    version=__version__,
    container_factory=container_factory,
)
app.mount("/static", DevAwareStaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


# BEFORE THE CATCH-ALL, and that ordering is the whole reason this route
# exists as code rather than as a file in static/.
#
# Browsers request /favicon.ico at the root on their own, without being
# told to. Without this, that request falls through to the shell handler
# below and receives an HTML document with a 200 — so the browser gets a
# successful response that is not an image, shows no icon, and gives
# nothing to diagnose. A 404 would at least be legible; a 200 of the wrong
# type is not.
@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> FileResponse:
    # Long max-age: the icon changes when the brand does, which is roughly
    # never, and a browser re-requesting it on every navigation is the
    # single most pointless request a site makes.
    return FileResponse(
        FAVICON,
        media_type="image/x-icon",
        headers={"Cache-Control": "public, max-age=604800, immutable"},
    )


@app.get("/{full_path:path}", response_class=HTMLResponse)
def shell(
    request: Request,
    full_path: str,
    settings: Annotated[Settings, Inject],
) -> HTMLResponse:
    # Every client route (``/``, deep links, refreshes) is served the same
    # Jinja shell, which injects the runtime config; React Router renders
    # the matching view. The ``/static`` mount, ``/healthz`` and the
    # favicon are registered earlier, so they never reach this catch-all.
    _ = full_path
    return templates.TemplateResponse(
        request,
        "index.html",
        {"version": __version__, "config": frontend_config(settings)},
    )


def run() -> None:
    """Console-script entrypoint (``shomer-ssr``)."""
    import uvicorn

    # A container or service manager must be able to reach it from
    # outside its own namespace.
    uvicorn.run("shomer_ssr.app:app", host="0.0.0.0", port=8080)  # noqa: S104

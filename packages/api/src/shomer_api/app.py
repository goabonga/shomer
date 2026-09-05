# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""The authorization API.

Built on `TripackAPI`, which owns the container's lifecycle and rewrites
every `Annotated[T, Inject]` parameter into a dependency FastAPI resolves.
Handlers therefore name interfaces from `shomer_lib.contracts` and never
the implementations behind them — swapping one is a change in the shared
module, not in this file.
"""

from __future__ import annotations

from typing import Annotated

from tripack_container import Container, Inject
from tripack_container.fastapi import TripackAPI

from shomer_lib.contracts import Clock, Settings
from shomer_lib.module import build_container

from . import __version__


def container_factory() -> Container:
    """Build the container the app runs on.

    A named function rather than a lambda so a test can substitute its own
    factory, and so the traceback of a wiring failure at startup names
    something findable.
    """
    return build_container()


app = TripackAPI(
    title="Shomer API",
    version=__version__,
    container_factory=container_factory,
)


@app.get("/healthz")
def healthz(clock: Annotated[Clock, Inject]) -> dict[str, object]:
    """Liveness probe.

    It reads the clock rather than returning a constant: a process that
    can still answer but can no longer resolve its dependencies is not
    healthy, and a hardcoded `{"status": "ok"}` cannot tell the two apart.
    """
    return {"status": "ok", "version": __version__, "time": clock.now()}


@app.get("/.well-known/openid-configuration")
def discovery(settings: Annotated[Settings, Inject]) -> dict[str, object]:
    """The OpenID Connect discovery document.

    Every URL is derived from the configured issuer, so an instance
    published under a different origin advertises endpoints that actually
    resolve. Only the endpoints that exist are listed — advertising a
    grant the server does not implement sends clients down a path that
    ends in a 404 they cannot interpret.
    """
    issuer = settings.issuer
    return {
        "issuer": issuer,
        "authorization_endpoint": f"{issuer}/oauth2/authorize",
        "token_endpoint": f"{issuer}/oauth2/token",
        "jwks_uri": f"{issuer}/.well-known/jwks.json",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        # PKCE is not optional here: the platform serves public clients,
        # and a public client without PKCE has no way to prove that the
        # code it redeems is the one it asked for.
        "code_challenge_methods_supported": ["S256"],
    }


def run() -> None:
    """Console-script entrypoint (`shomer-api`)."""
    import uvicorn

    # A container or service manager reaches the process from outside its
    # own namespace, so binding to localhost would make it unreachable
    # everywhere except a developer's laptop.
    uvicorn.run("shomer_api.app:app", host="0.0.0.0", port=8000)  # noqa: S104

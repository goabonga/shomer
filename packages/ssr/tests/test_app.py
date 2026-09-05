# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""Tests for the shomer-ssr routes."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from shomer_lib.settings import EnvSettings
from shomer_ssr import __version__
from shomer_ssr.app import STATIC_DIR, app, container_factory, frontend_config, run


@pytest.fixture(autouse=True)
def _isolated_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SHOMER_DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("SHOMER_ISSUER", "https://id.example.test")


@pytest.fixture
def client() -> Iterator[TestClient]:
    # The context manager runs the lifespan, and the lifespan builds the
    # container. Without it every injected parameter fails to resolve and
    # the failure reads as a routing problem.
    with TestClient(app) as test_client:
        yield test_client


def test_healthz_reports_the_running_version(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__}


def test_favicon_is_served_as_an_icon(client: TestClient) -> None:
    response = client.get("/favicon.ico")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/x-icon"
    assert "immutable" in response.headers["cache-control"]


def test_root_renders_the_shell(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert 'id="root"' in response.text
    assert "/static/main.js" in response.text


def test_unknown_route_renders_the_same_shell(client: TestClient) -> None:
    # Deep links and refreshes must not 404 — the browser resolves them.
    assert client.get("/somewhere/deep").text == client.get("/").text


def test_static_assets_are_mounted(client: TestClient) -> None:
    response = client.get("/static/main.js")
    assert response.status_code == 200


def test_frontend_config_carries_the_version_and_the_issuer() -> None:
    settings = EnvSettings(issuer="https://id.example.test")
    assert frontend_config(settings) == {
        "appName": "Shomer",
        "version": __version__,
        "issuer": "https://id.example.test",
    }


def test_the_shell_hands_the_browser_the_configured_issuer(
    client: TestClient,
) -> None:
    # The browser has to send the user to the same origin the tokens will
    # claim to come from; a second copy of that value drifts the first
    # time one deployment is reconfigured.
    assert "https://id.example.test" in client.get("/").text


def test_the_container_factory_builds_a_usable_container() -> None:
    from shomer_lib.contracts import Settings

    with container_factory() as container:
        assert container.resolve(Settings).issuer == "https://id.example.test"


def test_source_map_is_advertised_when_one_exists(client: TestClient) -> None:
    # The watch build writes main.js.map without appending the
    # `//# sourceMappingURL=` comment, so the header is the only thing
    # pointing DevTools at it. Create the map the way that build would,
    # and remove it again — a release build ships no map, and leaving one
    # behind would make the next test run lie.
    map_file = STATIC_DIR / "main.js.map"
    map_file.write_text("{}")
    try:
        response = client.get("/static/main.js")
        assert response.headers["SourceMap"] == "/static/main.js.map"
    finally:
        map_file.unlink()

    # And no header at all once it is gone.
    assert "SourceMap" not in client.get("/static/main.js").headers


def test_run_serves_on_every_interface(monkeypatch: pytest.MonkeyPatch) -> None:
    # A container or service manager reaches the process from outside its
    # own namespace, so binding to localhost would make it unreachable
    # everywhere except a developer's laptop.
    called: dict[str, object] = {}

    def fake_run(target: str, **kwargs: object) -> None:
        called["target"] = target
        called.update(kwargs)

    monkeypatch.setattr("uvicorn.run", fake_run)
    run()

    assert called["target"] == "shomer_ssr.app:app"
    assert called["host"] == "0.0.0.0"
    assert called["port"] == 8080

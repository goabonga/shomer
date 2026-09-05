# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""Tests for the authorization API."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from shomer_api import __version__
from shomer_api.app import app, container_factory, run


@pytest.fixture(autouse=True)
def _isolated_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SHOMER_DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("SHOMER_ISSUER", "https://id.example.test")


@pytest.fixture
def client() -> Iterator[TestClient]:
    # The context manager is what runs the lifespan, and the lifespan is
    # what builds the container. Without it every injected parameter
    # fails to resolve and the failure looks like a routing problem.
    with TestClient(app) as test_client:
        yield test_client


def test_healthz_resolves_the_injected_clock(client: TestClient) -> None:
    body = client.get("/healthz").json()
    assert body["status"] == "ok"
    assert body["version"] == __version__
    assert body["time"] > 0


def test_discovery_derives_every_url_from_the_issuer(client: TestClient) -> None:
    body = client.get("/.well-known/openid-configuration").json()
    assert body["issuer"] == "https://id.example.test"
    assert body["token_endpoint"] == "https://id.example.test/oauth2/token"
    assert body["authorization_endpoint"] == (
        "https://id.example.test/oauth2/authorize"
    )
    assert body["jwks_uri"] == "https://id.example.test/.well-known/jwks.json"


def test_discovery_requires_pkce(client: TestClient) -> None:
    # A public client without PKCE cannot prove the code it redeems is the
    # one it asked for, so advertising anything else here would be wrong.
    body = client.get("/.well-known/openid-configuration").json()
    assert body["code_challenge_methods_supported"] == ["S256"]


def test_discovery_advertises_only_implemented_grants(client: TestClient) -> None:
    body = client.get("/.well-known/openid-configuration").json()
    assert body["grant_types_supported"] == ["authorization_code"]
    assert body["response_types_supported"] == ["code"]


def test_the_container_factory_builds_a_usable_container() -> None:
    from shomer_lib.contracts import Settings

    with container_factory() as container:
        assert container.resolve(Settings).issuer == "https://id.example.test"


def test_run_serves_on_every_interface(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict[str, object] = {}

    def fake_run(target: str, **kwargs: object) -> None:
        called["target"] = target
        called.update(kwargs)

    monkeypatch.setattr("uvicorn.run", fake_run)
    run()

    assert called["target"] == "shomer_api.app:app"
    assert called["host"] == "0.0.0.0"
    assert called["port"] == 8000

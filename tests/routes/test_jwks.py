# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Integration tests for GET /.well-known/jwks.json."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any, Callable
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from shomer.app import app
from shomer.deps import get_db
from shomer.models.jwk import JWK, JWKStatus
from shomer.routes.jwks import JWKS_CACHE_MAX_AGE


def _make_jwk(kid: str, status: JWKStatus = JWKStatus.ACTIVE) -> JWK:
    """Build a JWK stub with a valid public_key JSON."""
    jwk = JWK(
        kid=kid,
        algorithm="RS256",
        public_key=json.dumps(
            {
                "kty": "RSA",
                "kid": kid,
                "alg": "RS256",
                "use": "sig",
                "n": "abc",
                "e": "AQAB",
            }
        ),
        private_key_enc=b"encrypted",
        status=status,
    )
    return jwk


def _mock_session(keys: list[JWK]) -> Callable[..., Any]:
    """Create a mock async session returning the given keys."""

    async def _get_db_override() -> AsyncIterator[AsyncMock]:
        mock = AsyncMock()
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = keys
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        mock.execute.return_value = result_mock
        yield mock

    return _get_db_override


@pytest.fixture(autouse=True)
def _restore_deps() -> Iterator[None]:
    """Restore dependency overrides after each test."""
    yield
    app.dependency_overrides.clear()


class TestJWKSEndpoint:
    """Tests for GET /.well-known/jwks.json."""

    def test_returns_empty_keyset(self) -> None:
        import asyncio

        app.dependency_overrides[get_db] = _mock_session([])

        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.get("/.well-known/jwks.json")
                assert resp.status_code == 200
                body = resp.json()
                assert body == {"keys": []}

        asyncio.run(_run())

    def test_returns_active_and_rotated_keys(self) -> None:
        import asyncio

        keys = [
            _make_jwk("key-1", JWKStatus.ACTIVE),
            _make_jwk("key-2", JWKStatus.ROTATED),
        ]
        app.dependency_overrides[get_db] = _mock_session(keys)

        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.get("/.well-known/jwks.json")
                assert resp.status_code == 200
                body = resp.json()
                assert len(body["keys"]) == 2
                kids = {k["kid"] for k in body["keys"]}
                assert kids == {"key-1", "key-2"}

        asyncio.run(_run())

    def test_cache_control_header(self) -> None:
        import asyncio

        app.dependency_overrides[get_db] = _mock_session([])

        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.get("/.well-known/jwks.json")
                cc = resp.headers.get("cache-control", "")
                assert f"max-age={JWKS_CACHE_MAX_AGE}" in cc
                assert "public" in cc

        asyncio.run(_run())

    def test_keys_contain_rfc7517_fields(self) -> None:
        import asyncio

        keys = [_make_jwk("rfc-test")]
        app.dependency_overrides[get_db] = _mock_session(keys)

        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.get("/.well-known/jwks.json")
                key = resp.json()["keys"][0]
                assert key["kty"] == "RSA"
                assert key["kid"] == "rfc-test"
                assert key["alg"] == "RS256"
                assert key["use"] == "sig"
                assert "n" in key
                assert "e" in key

        asyncio.run(_run())

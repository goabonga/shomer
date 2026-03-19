# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Pure unit tests for JWKS endpoint."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

from shomer.routes.jwks import JWKS_CACHE_MAX_AGE, jwks_endpoint


def _mock_key(kid: str = "k1") -> MagicMock:
    """Create a mock JWK row."""
    k = MagicMock()
    k.public_key = json.dumps(
        {
            "kty": "RSA",
            "kid": kid,
            "alg": "RS256",
            "use": "sig",
            "n": "abc",
            "e": "AQAB",
        }
    )
    return k


class TestJWKSEndpoint:
    """Unit tests for GET /.well-known/jwks.json."""

    def test_empty_keyset(self) -> None:
        """No keys returns empty keys array."""

        async def _run() -> None:
            db = AsyncMock()
            result_mock = MagicMock()
            result_mock.scalars.return_value.all.return_value = []
            db.execute.return_value = result_mock

            resp = await jwks_endpoint(db)
            body = json.loads(bytes(resp.body))
            assert body == {"keys": []}

        asyncio.run(_run())

    def test_returns_keys(self) -> None:
        """Active keys are included in the response."""

        async def _run() -> None:
            db = AsyncMock()
            result_mock = MagicMock()
            result_mock.scalars.return_value.all.return_value = [
                _mock_key("k1"),
                _mock_key("k2"),
            ]
            db.execute.return_value = result_mock

            resp = await jwks_endpoint(db)
            body = json.loads(bytes(resp.body))
            assert len(body["keys"]) == 2
            assert body["keys"][0]["kid"] == "k1"
            assert body["keys"][1]["kid"] == "k2"

        asyncio.run(_run())

    def test_cache_control_header(self) -> None:
        """Response includes Cache-Control header."""

        async def _run() -> None:
            db = AsyncMock()
            result_mock = MagicMock()
            result_mock.scalars.return_value.all.return_value = []
            db.execute.return_value = result_mock

            resp = await jwks_endpoint(db)
            cc = resp.headers.get("cache-control", "")
            assert f"max-age={JWKS_CACHE_MAX_AGE}" in cc

        asyncio.run(_run())

    def test_keys_have_rfc7517_fields(self) -> None:
        """Each key contains the required RFC 7517 fields."""

        async def _run() -> None:
            db = AsyncMock()
            result_mock = MagicMock()
            result_mock.scalars.return_value.all.return_value = [_mock_key()]
            db.execute.return_value = result_mock

            resp = await jwks_endpoint(db)
            body = json.loads(bytes(resp.body))
            key = body["keys"][0]
            for field in ("kty", "kid", "alg", "use", "n", "e"):
                assert field in key, f"Missing field: {field}"

        asyncio.run(_run())

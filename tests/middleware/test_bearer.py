# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for Bearer token extraction middleware."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from shomer.middleware.bearer import extract_bearer_token


def _req(auth_header: str | None = None) -> MagicMock:
    """Create a mock request with an optional Authorization header."""
    r = MagicMock()
    r.headers = MagicMock()
    r.headers.get = lambda k, d=None: auth_header if k == "authorization" else d
    return r


class TestExtractBearerToken:
    """Tests for extract_bearer_token()."""

    def test_valid_bearer_token(self) -> None:
        """Valid 'Bearer <token>' returns the token."""

        async def _run() -> None:
            token = await extract_bearer_token(_req("Bearer my-jwt-token"))
            assert token == "my-jwt-token"

        asyncio.run(_run())

    def test_missing_header_raises_401(self) -> None:
        """Missing Authorization header raises 401."""

        async def _run() -> None:
            with pytest.raises(HTTPException) as exc_info:
                await extract_bearer_token(_req(None))
            assert exc_info.value.status_code == 401
            headers = exc_info.value.headers or {}
            assert headers["WWW-Authenticate"] == "Bearer"

        asyncio.run(_run())

    def test_empty_header_raises_401(self) -> None:
        """Empty Authorization header raises 401."""

        async def _run() -> None:
            with pytest.raises(HTTPException) as exc_info:
                await extract_bearer_token(_req(""))
            assert exc_info.value.status_code == 401

        asyncio.run(_run())

    def test_non_bearer_scheme_raises_401(self) -> None:
        """Non-Bearer scheme (e.g. Basic) raises 401."""

        async def _run() -> None:
            with pytest.raises(HTTPException) as exc_info:
                await extract_bearer_token(_req("Basic dXNlcjpwYXNz"))
            assert exc_info.value.status_code == 401
            assert "Bearer" in str(exc_info.value.detail)

        asyncio.run(_run())

    def test_bearer_without_token_raises_401(self) -> None:
        """'Bearer' without a token raises 401."""

        async def _run() -> None:
            with pytest.raises(HTTPException) as exc_info:
                await extract_bearer_token(_req("Bearer "))
            assert exc_info.value.status_code == 401

        asyncio.run(_run())

    def test_bearer_case_insensitive(self) -> None:
        """'bearer' (lowercase) is accepted."""

        async def _run() -> None:
            token = await extract_bearer_token(_req("bearer my-token"))
            assert token == "my-token"

        asyncio.run(_run())

    def test_bearer_mixed_case(self) -> None:
        """'BEARER' (uppercase) is accepted."""

        async def _run() -> None:
            token = await extract_bearer_token(_req("BEARER my-token"))
            assert token == "my-token"

        asyncio.run(_run())

    def test_token_with_dots_preserved(self) -> None:
        """JWT-like token with dots is preserved as-is."""

        async def _run() -> None:
            jwt = "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIxIn0.sig"
            token = await extract_bearer_token(_req(f"Bearer {jwt}"))
            assert token == jwt

        asyncio.run(_run())

    def test_www_authenticate_header_on_error(self) -> None:
        """All 401 responses include WWW-Authenticate: Bearer."""

        async def _run() -> None:
            for header in [None, "", "Basic x", "Bearer "]:
                with pytest.raises(HTTPException) as exc_info:
                    await extract_bearer_token(_req(header))
                assert exc_info.value.headers is not None
                headers = exc_info.value.headers or {}
            assert headers["WWW-Authenticate"] == "Bearer"

        asyncio.run(_run())

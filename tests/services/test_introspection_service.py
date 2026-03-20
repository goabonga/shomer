# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for token introspection service."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from shomer.services.introspection_service import IntrospectionService


class TestIntrospectAccessToken:
    """Tests for access token introspection."""

    @patch("jwt.decode")
    def test_active_access_token(self, mock_decode: MagicMock) -> None:
        """Valid non-revoked access token returns active=True with claims."""
        mock_decode.return_value = {
            "jti": "j1",
            "sub": "user-1",
            "aud": "client-1",
            "iss": "https://auth.local",
            "scope": "openid profile",
            "iat": 1700000000,
        }

        async def _run() -> None:
            db = AsyncMock()
            mock_at = MagicMock()
            mock_at.jti = "j1"
            mock_at.client_id = "client-1"
            mock_at.revoked = False
            mock_at.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_at
            db.execute.return_value = result

            svc = IntrospectionService(db)
            resp = await svc.introspect(token="jwt", token_type_hint="access_token")
            assert resp["active"] is True
            assert resp["scope"] == "openid profile"
            assert resp["client_id"] == "client-1"
            assert resp["token_type"] == "Bearer"
            assert resp["sub"] == "user-1"

        asyncio.run(_run())

    @patch("jwt.decode")
    def test_revoked_access_token(self, mock_decode: MagicMock) -> None:
        """Revoked access token returns active=False."""
        mock_decode.return_value = {"jti": "j1"}

        async def _run() -> None:
            db = AsyncMock()
            mock_at = MagicMock()
            mock_at.revoked = True
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_at
            db.execute.return_value = result

            svc = IntrospectionService(db)
            resp = await svc.introspect(token="jwt", token_type_hint="access_token")
            assert resp["active"] is False

        asyncio.run(_run())

    @patch("jwt.decode")
    def test_expired_access_token(self, mock_decode: MagicMock) -> None:
        """Expired access token returns active=False."""
        mock_decode.return_value = {"jti": "j1"}

        async def _run() -> None:
            db = AsyncMock()
            mock_at = MagicMock()
            mock_at.revoked = False
            mock_at.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_at
            db.execute.return_value = result

            svc = IntrospectionService(db)
            resp = await svc.introspect(token="jwt", token_type_hint="access_token")
            assert resp["active"] is False

        asyncio.run(_run())

    def test_invalid_jwt(self) -> None:
        """Invalid JWT returns active=False."""

        async def _run() -> None:
            db = AsyncMock()
            svc = IntrospectionService(db)
            resp = await svc.introspect(token="not-jwt", token_type_hint="access_token")
            assert resp["active"] is False

        asyncio.run(_run())

    @patch("jwt.decode")
    def test_unknown_jti(self, mock_decode: MagicMock) -> None:
        """JWT with unknown jti returns active=False."""
        mock_decode.return_value = {"jti": "unknown"}

        async def _run() -> None:
            db = AsyncMock()
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db.execute.return_value = result

            svc = IntrospectionService(db)
            resp = await svc.introspect(token="jwt", token_type_hint="access_token")
            assert resp["active"] is False

        asyncio.run(_run())


class TestIntrospectRefreshToken:
    """Tests for refresh token introspection."""

    def test_active_refresh_token(self) -> None:
        """Valid non-revoked refresh token returns active=True."""

        async def _run() -> None:
            db = AsyncMock()
            uid = uuid.uuid4()
            mock_rt = MagicMock()
            mock_rt.revoked = False
            mock_rt.scopes = "openid"
            mock_rt.client_id = "client-1"
            mock_rt.user_id = uid
            mock_rt.expires_at = datetime.now(timezone.utc) + timedelta(days=30)

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_rt
            db.execute.return_value = result

            svc = IntrospectionService(db)
            resp = await svc.introspect(
                token="refresh-tok", token_type_hint="refresh_token"
            )
            assert resp["active"] is True
            assert resp["token_type"] == "refresh_token"
            assert resp["client_id"] == "client-1"
            assert resp["sub"] == str(uid)

        asyncio.run(_run())

    def test_revoked_refresh_token(self) -> None:
        """Revoked refresh token returns active=False."""

        async def _run() -> None:
            db = AsyncMock()
            mock_rt = MagicMock()
            mock_rt.revoked = True
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_rt
            db.execute.return_value = result

            svc = IntrospectionService(db)
            resp = await svc.introspect(token="tok", token_type_hint="refresh_token")
            assert resp["active"] is False

        asyncio.run(_run())

    def test_unknown_refresh_token(self) -> None:
        """Unknown refresh token returns active=False."""

        async def _run() -> None:
            db = AsyncMock()
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db.execute.return_value = result

            svc = IntrospectionService(db)
            resp = await svc.introspect(
                token="unknown", token_type_hint="refresh_token"
            )
            assert resp["active"] is False

        asyncio.run(_run())


class TestIntrospectNoHint:
    """Tests for introspection without token_type_hint."""

    @patch("jwt.decode")
    def test_tries_access_first(self, mock_decode: MagicMock) -> None:
        """Without hint, tries access token first."""
        mock_decode.return_value = {
            "jti": "j1",
            "sub": "u",
            "scope": "openid",
            "iat": 1700000000,
        }

        async def _run() -> None:
            db = AsyncMock()
            mock_at = MagicMock()
            mock_at.revoked = False
            mock_at.client_id = "c"
            mock_at.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_at
            db.execute.return_value = result

            svc = IntrospectionService(db)
            resp = await svc.introspect(token="jwt", token_type_hint=None)
            assert resp["active"] is True
            assert resp["token_type"] == "Bearer"

        asyncio.run(_run())

    def test_falls_back_to_refresh(self) -> None:
        """If not a valid access token, tries refresh."""

        async def _run() -> None:
            db = AsyncMock()
            uid = uuid.uuid4()

            # Access token: invalid JWT → active=False
            # Refresh token: found
            mock_rt = MagicMock()
            mock_rt.revoked = False
            mock_rt.scopes = "openid"
            mock_rt.client_id = "c"
            mock_rt.user_id = uid
            mock_rt.expires_at = datetime.now(timezone.utc) + timedelta(days=30)

            refresh_result = MagicMock()
            refresh_result.scalar_one_or_none.return_value = mock_rt
            db.execute.return_value = refresh_result

            svc = IntrospectionService(db)
            resp = await svc.introspect(token="raw-refresh", token_type_hint=None)
            assert resp["active"] is True
            assert resp["token_type"] == "refresh_token"

        asyncio.run(_run())

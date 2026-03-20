# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for token revocation service."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from shomer.services.revocation_service import RevocationService


class TestRevokeRefreshToken:
    """Tests for refresh token revocation."""

    def test_revokes_family(self) -> None:
        """Revoking a refresh token revokes the entire family."""

        async def _run() -> None:
            db = AsyncMock()
            db.flush = AsyncMock()

            mock_rt = MagicMock()
            mock_rt.family_id = "family-1"
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_rt
            db.execute.side_effect = [result, AsyncMock()]  # SELECT + UPDATE

            svc = RevocationService(db)
            await svc.revoke(
                token="raw-refresh",
                token_type_hint="refresh_token",
                client_id="client-1",
            )
            assert db.execute.call_count == 2

        asyncio.run(_run())

    def test_unknown_token_no_error(self) -> None:
        """Unknown refresh token does not raise."""

        async def _run() -> None:
            db = AsyncMock()
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db.execute.return_value = result

            svc = RevocationService(db)
            await svc.revoke(
                token="unknown",
                token_type_hint="refresh_token",
                client_id="c",
            )

        asyncio.run(_run())


class TestRevokeAccessToken:
    """Tests for access token revocation."""

    @patch("jwt.decode")
    def test_revokes_access_token(self, mock_decode: MagicMock) -> None:
        """Valid access token JWT gets revoked."""
        mock_decode.return_value = {"jti": "jti-1"}

        async def _run() -> None:
            db = AsyncMock()
            db.flush = AsyncMock()
            mock_at = MagicMock()
            mock_at.revoked = False
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_at
            db.execute.return_value = result

            svc = RevocationService(db)
            await svc.revoke(
                token="jwt-token",
                token_type_hint="access_token",
                client_id="c",
            )
            assert mock_at.revoked is True

        asyncio.run(_run())

    def test_invalid_jwt_no_error(self) -> None:
        """Invalid JWT does not raise."""

        async def _run() -> None:
            db = AsyncMock()
            svc = RevocationService(db)
            await svc.revoke(
                token="not-a-jwt",
                token_type_hint="access_token",
                client_id="c",
            )

        asyncio.run(_run())

    @patch("jwt.decode")
    def test_unknown_jti_no_error(self, mock_decode: MagicMock) -> None:
        """JWT with unknown jti does not raise."""
        mock_decode.return_value = {"jti": "unknown-jti"}

        async def _run() -> None:
            db = AsyncMock()
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db.execute.return_value = result

            svc = RevocationService(db)
            await svc.revoke(
                token="jwt",
                token_type_hint="access_token",
                client_id="c",
            )

        asyncio.run(_run())


class TestRevokeNoHint:
    """Tests for revocation without token_type_hint."""

    def test_tries_refresh_first(self) -> None:
        """Without hint, tries refresh token first."""

        async def _run() -> None:
            db = AsyncMock()
            db.flush = AsyncMock()

            mock_rt = MagicMock()
            mock_rt.family_id = "f1"
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_rt
            db.execute.side_effect = [result, AsyncMock()]

            svc = RevocationService(db)
            await svc.revoke(token="tok", token_type_hint=None, client_id="c")
            # Only 2 calls: SELECT refresh + UPDATE family (no access attempt)
            assert db.execute.call_count == 2

        asyncio.run(_run())

    @patch("jwt.decode")
    def test_falls_back_to_access(self, mock_decode: MagicMock) -> None:
        """If not a refresh token, tries access token."""
        mock_decode.return_value = {"jti": "j1"}

        async def _run() -> None:
            db = AsyncMock()
            db.flush = AsyncMock()

            # Refresh not found
            refresh_result = MagicMock()
            refresh_result.scalar_one_or_none.return_value = None
            # Access found
            mock_at = MagicMock()
            mock_at.revoked = False
            access_result = MagicMock()
            access_result.scalar_one_or_none.return_value = mock_at

            db.execute.side_effect = [refresh_result, access_result]

            svc = RevocationService(db)
            await svc.revoke(token="jwt-tok", token_type_hint=None, client_id="c")
            assert mock_at.revoked is True

        asyncio.run(_run())

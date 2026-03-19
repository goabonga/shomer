# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for sliding session expiration middleware."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from shomer.middleware.session import SessionMiddleware


class TestSessionMiddleware:
    """Tests for SessionMiddleware.dispatch()."""

    def test_no_cookie_passes_through(self) -> None:
        """No session cookie — middleware does nothing."""

        async def _run() -> None:
            mock_request = MagicMock()
            mock_request.cookies.get.return_value = None
            mock_response = MagicMock()
            mock_call_next = AsyncMock(return_value=mock_response)

            middleware = SessionMiddleware(app=MagicMock())
            result = await middleware.dispatch(mock_request, mock_call_next)
            assert result == mock_response
            mock_call_next.assert_awaited_once()

        asyncio.run(_run())

    def test_invalid_cookie_passes_through(self) -> None:
        """Invalid session token — middleware passes through."""

        async def _run() -> None:
            mock_svc = AsyncMock()
            mock_svc.validate.return_value = None
            mock_db = AsyncMock()
            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_db
            mock_cm.__aexit__.return_value = False

            mock_request = MagicMock()
            mock_request.cookies.get.return_value = "invalid-tok"
            mock_response = MagicMock()
            mock_call_next = AsyncMock(return_value=mock_response)

            middleware = SessionMiddleware(app=MagicMock())

            with (
                patch(
                    "shomer.middleware.session.async_session",
                    return_value=mock_cm,
                ),
                patch(
                    "shomer.middleware.session.SessionService",
                    return_value=mock_svc,
                ),
            ):
                result = await middleware.dispatch(mock_request, mock_call_next)

            mock_svc.renew.assert_not_awaited()
            assert result == mock_response

        asyncio.run(_run())

    def test_renew_called_for_valid_session(self) -> None:
        """Middleware calls renew() and commit() for valid sessions."""

        async def _run() -> None:
            mock_session = MagicMock()
            mock_svc = AsyncMock()
            mock_svc.validate.return_value = mock_session
            mock_db = AsyncMock()
            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_db
            mock_cm.__aexit__.return_value = False

            mock_request = MagicMock()
            mock_request.cookies.get.return_value = "valid-token"

            mock_response = MagicMock()
            mock_call_next = AsyncMock(return_value=mock_response)

            middleware = SessionMiddleware(app=MagicMock())

            with (
                patch(
                    "shomer.middleware.session.async_session",
                    return_value=mock_cm,
                ),
                patch(
                    "shomer.middleware.session.SessionService",
                    return_value=mock_svc,
                ),
            ):
                result = await middleware.dispatch(mock_request, mock_call_next)

            mock_svc.validate.assert_awaited_once_with("valid-token")
            mock_svc.renew.assert_awaited_once_with(mock_session)
            mock_db.commit.assert_awaited_once()
            assert result == mock_response

        asyncio.run(_run())

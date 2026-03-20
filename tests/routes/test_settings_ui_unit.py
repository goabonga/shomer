# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for user settings UI routes."""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from shomer.routes.settings_ui import (
    _get_session_user,
    settings_emails,
    settings_profile,
    settings_security,
)


def _req(cookies: dict[str, str] | None = None) -> MagicMock:
    cookie_data = cookies or {}
    r = MagicMock()
    r.cookies = MagicMock()
    r.cookies.get = lambda k, d=None: cookie_data.get(k, d)
    return r


def _mock_user() -> MagicMock:
    u = MagicMock()
    u.id = uuid.uuid4()
    u.username = "testuser"
    u.profile = MagicMock(name="Test", locale="en-US")
    e = MagicMock()
    e.email = "test@example.com"
    e.is_primary = True
    e.is_verified = True
    u.emails = [e]
    return u


class TestGetSessionUser:
    """Tests for _get_session_user()."""

    def test_no_cookie_returns_none(self) -> None:
        async def _run() -> None:
            result = await _get_session_user(_req(), AsyncMock())
            assert result is None

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui.SessionService")
    def test_invalid_session_returns_none(self, mock_cls: MagicMock) -> None:
        async def _run() -> None:
            mock_svc = AsyncMock()
            mock_svc.validate.return_value = None
            mock_cls.return_value = mock_svc
            result = await _get_session_user(_req({"session_id": "bad"}), AsyncMock())
            assert result is None

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui.SessionService")
    def test_valid_session_returns_tuple(self, mock_cls: MagicMock) -> None:
        async def _run() -> None:
            mock_session = MagicMock(user_id=uuid.uuid4())
            mock_svc = AsyncMock()
            mock_svc.validate.return_value = mock_session
            mock_cls.return_value = mock_svc

            db = AsyncMock()
            mock_user = _mock_user()
            result_mock = MagicMock()
            result_mock.scalar_one_or_none.return_value = mock_user
            db.execute.return_value = result_mock

            result = await _get_session_user(_req({"session_id": "good"}), db)
            assert result is not None
            assert result[1].username == "testuser"

        asyncio.run(_run())


class TestSettingsProfile:
    """Tests for GET /ui/settings/profile."""

    @patch("shomer.routes.settings_ui._get_session_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        async def _run() -> None:
            mock_auth.return_value = None
            resp = await settings_profile(_req(), AsyncMock())
            assert resp.status_code == 302
            assert "/ui/login" in resp.headers["location"]

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_authenticated_renders_page(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        async def _run() -> None:
            mock_user = _mock_user()
            mock_auth.return_value = (MagicMock(), mock_user)
            mock_render.return_value = "html"
            await settings_profile(_req({"session_id": "tok"}), AsyncMock())
            mock_render.assert_called_once()
            ctx = mock_render.call_args[0][2]
            assert ctx["section"] == "profile"
            assert ctx["user"] is mock_user

        asyncio.run(_run())


class TestSettingsEmails:
    """Tests for GET /ui/settings/emails."""

    @patch("shomer.routes.settings_ui._get_session_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        async def _run() -> None:
            mock_auth.return_value = None
            resp = await settings_emails(_req(), AsyncMock())
            assert resp.status_code == 302

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_authenticated_renders_page(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        async def _run() -> None:
            mock_user = _mock_user()
            mock_auth.return_value = (MagicMock(), mock_user)
            mock_render.return_value = "html"
            await settings_emails(_req({"session_id": "tok"}), AsyncMock())
            ctx = mock_render.call_args[0][2]
            assert ctx["section"] == "emails"
            assert len(ctx["emails"]) == 1

        asyncio.run(_run())


class TestSettingsSecurity:
    """Tests for GET /ui/settings/security."""

    @patch("shomer.routes.settings_ui._get_session_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        async def _run() -> None:
            mock_auth.return_value = None
            resp = await settings_security(_req(), AsyncMock())
            assert resp.status_code == 302

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_authenticated_renders_page(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        async def _run() -> None:
            mock_user = _mock_user()
            mock_session = MagicMock()
            mock_auth.return_value = (mock_session, mock_user)

            db = AsyncMock()
            count_result = MagicMock()
            count_result.scalar.return_value = 2
            db.execute.return_value = count_result

            mock_render.return_value = "html"
            await settings_security(_req({"session_id": "tok"}), db)
            ctx = mock_render.call_args[0][2]
            assert ctx["section"] == "security"
            assert ctx["active_sessions"] == 2

        asyncio.run(_run())

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for device code verification UI."""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from shomer.routes.device_ui import (
    _get_session_user_id,
    device_verify_page,
    device_verify_submit,
)
from shomer.services.device_auth_service import DeviceAuthError


def _req(cookies: dict[str, str] | None = None) -> MagicMock:
    cookie_data = cookies or {}
    r = MagicMock()
    r.cookies = MagicMock()
    r.cookies.get = lambda k, d=None: cookie_data.get(k, d)
    return r


class TestGetSessionUserId:
    """Tests for _get_session_user_id."""

    def test_no_cookie_returns_none(self) -> None:
        async def _run() -> None:
            result = await _get_session_user_id(_req(), AsyncMock())
            assert result is None

        asyncio.run(_run())

    @patch("shomer.routes.device_ui.SessionService")
    def test_invalid_session_returns_none(self, mock_cls: MagicMock) -> None:
        async def _run() -> None:
            mock_svc = AsyncMock()
            mock_svc.validate.return_value = None
            mock_cls.return_value = mock_svc
            result = await _get_session_user_id(
                _req({"session_id": "bad"}), AsyncMock()
            )
            assert result is None

        asyncio.run(_run())

    @patch("shomer.routes.device_ui.SessionService")
    def test_valid_session_returns_user_id(self, mock_cls: MagicMock) -> None:
        async def _run() -> None:
            uid = uuid.uuid4()
            mock_session = MagicMock(user_id=uid)
            mock_svc = AsyncMock()
            mock_svc.validate.return_value = mock_session
            mock_cls.return_value = mock_svc
            result = await _get_session_user_id(_req({"session_id": "ok"}), AsyncMock())
            assert result == uid

        asyncio.run(_run())


class TestDeviceVerifyPage:
    """Tests for GET /ui/device."""

    @patch("shomer.routes.device_ui._get_session_user_id")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        async def _run() -> None:
            mock_auth.return_value = None
            resp = await device_verify_page(_req(), AsyncMock())
            assert resp.status_code == 302
            assert "/ui/login" in resp.headers["location"]

        asyncio.run(_run())

    @patch("shomer.routes.device_ui._render")
    @patch("shomer.routes.device_ui._get_session_user_id")
    def test_authenticated_renders_page(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        async def _run() -> None:
            mock_auth.return_value = uuid.uuid4()
            mock_render.return_value = "html"
            await device_verify_page(_req({"session_id": "tok"}), AsyncMock())
            mock_render.assert_called_once()
            ctx = mock_render.call_args[0][2]
            assert "user_code" in ctx

        asyncio.run(_run())

    @patch("shomer.routes.device_ui._render")
    @patch("shomer.routes.device_ui._get_session_user_id")
    def test_autofill_user_code(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        async def _run() -> None:
            mock_auth.return_value = uuid.uuid4()
            mock_render.return_value = "html"
            await device_verify_page(
                _req({"session_id": "tok"}), AsyncMock(), user_code="ABCD-EFGH"
            )
            ctx = mock_render.call_args[0][2]
            assert ctx["user_code"] == "ABCD-EFGH"

        asyncio.run(_run())


class TestDeviceVerifySubmit:
    """Tests for POST /ui/device."""

    @patch("shomer.routes.device_ui._get_session_user_id")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        async def _run() -> None:
            mock_auth.return_value = None
            resp = await device_verify_submit(
                _req(), AsyncMock(), "ABCD-EFGH", "approve"
            )
            assert resp.status_code == 302

        asyncio.run(_run())

    @patch("shomer.routes.device_ui.DeviceAuthService")
    @patch("shomer.routes.device_ui._render")
    @patch("shomer.routes.device_ui._get_session_user_id")
    def test_approve_success(
        self, mock_auth: AsyncMock, mock_render: MagicMock, mock_svc_cls: MagicMock
    ) -> None:
        async def _run() -> None:
            mock_auth.return_value = uuid.uuid4()
            mock_svc = AsyncMock()
            mock_svc_cls.return_value = mock_svc
            mock_render.return_value = "html"
            await device_verify_submit(
                _req({"session_id": "tok"}), AsyncMock(), "ABCD-EFGH", "approve"
            )
            mock_svc.approve.assert_awaited_once()
            ctx = mock_render.call_args[0][2]
            assert "success" in ctx

        asyncio.run(_run())

    @patch("shomer.routes.device_ui.DeviceAuthService")
    @patch("shomer.routes.device_ui._render")
    @patch("shomer.routes.device_ui._get_session_user_id")
    def test_deny_success(
        self, mock_auth: AsyncMock, mock_render: MagicMock, mock_svc_cls: MagicMock
    ) -> None:
        async def _run() -> None:
            mock_auth.return_value = uuid.uuid4()
            mock_svc = AsyncMock()
            mock_svc_cls.return_value = mock_svc
            mock_render.return_value = "html"
            await device_verify_submit(
                _req({"session_id": "tok"}), AsyncMock(), "ABCD-EFGH", "deny"
            )
            mock_svc.deny.assert_awaited_once()
            ctx = mock_render.call_args[0][2]
            assert "denied" in ctx["success"].lower()

        asyncio.run(_run())

    @patch("shomer.routes.device_ui.DeviceAuthService")
    @patch("shomer.routes.device_ui._render")
    @patch("shomer.routes.device_ui._get_session_user_id")
    def test_invalid_code_shows_error(
        self, mock_auth: AsyncMock, mock_render: MagicMock, mock_svc_cls: MagicMock
    ) -> None:
        async def _run() -> None:
            mock_auth.return_value = uuid.uuid4()
            mock_svc = AsyncMock()
            mock_svc.approve.side_effect = DeviceAuthError(
                "invalid_grant", "Unknown user code"
            )
            mock_svc_cls.return_value = mock_svc
            mock_render.return_value = "html"
            await device_verify_submit(
                _req({"session_id": "tok"}), AsyncMock(), "XXXX-XXXX", "approve"
            )
            ctx = mock_render.call_args[0][2]
            assert "error" in ctx

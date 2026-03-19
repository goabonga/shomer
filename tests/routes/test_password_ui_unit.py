# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Pure unit tests for password UI route handlers."""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from shomer.routes.password_ui import (
    change_password_page,
    change_password_submit,
    forgot_password_page,
    forgot_password_submit,
    reset_password_page,
    reset_password_submit,
)
from shomer.services.auth_service import InvalidCredentialsError, InvalidResetTokenError


def _req(cookies: dict[str, str] | None = None) -> MagicMock:
    cookie_data = cookies or {}
    r = MagicMock()
    r.cookies = MagicMock()
    r.cookies.get = lambda k, d=None: cookie_data.get(k, d)
    return r


class TestRenderHelper:
    """Tests for _templates() and _render() helpers."""

    @patch("shomer.routes.password_ui._templates")
    def test_render_calls_template_response(self, mock_tpl: MagicMock) -> None:
        from shomer.routes.password_ui import _render

        mock_tpl.return_value.TemplateResponse.return_value = "resp"
        result = _render(MagicMock(), "test.html", {"k": "v"})
        assert result == "resp"

    def test_templates_returns_jinja(self) -> None:
        from shomer.routes.password_ui import _templates

        result = _templates()
        assert result is not None


class TestForgotPasswordPage:
    """GET /ui/password/reset."""

    @patch("shomer.routes.password_ui._render")
    def test_renders_page(self, mock_render: MagicMock) -> None:
        asyncio.run(forgot_password_page(_req()))
        mock_render.assert_called_once()
        assert "forgot_password" in mock_render.call_args[0][1]


class TestForgotPasswordSubmit:
    """POST /ui/password/reset."""

    @patch("shomer.routes.password_ui.send_email_task")
    @patch("shomer.routes.password_ui.AuthService")
    @patch("shomer.routes.password_ui._render")
    def test_submit_shows_success(
        self, mock_render: MagicMock, mock_cls: MagicMock, mock_task: MagicMock
    ) -> None:
        mock_svc = AsyncMock()
        mock_svc.request_password_reset.return_value = uuid.uuid4()
        mock_cls.return_value = mock_svc
        asyncio.run(forgot_password_submit(_req(), AsyncMock(), "a@b.com"))
        mock_task.delay.assert_called_once()
        ctx = mock_render.call_args[0][2]
        assert "success" in ctx


class TestResetPasswordPage:
    """GET /ui/password/reset-verify."""

    @patch("shomer.routes.password_ui._render")
    def test_renders_page(self, mock_render: MagicMock) -> None:
        asyncio.run(reset_password_page(_req()))
        mock_render.assert_called_once()

    @patch("shomer.routes.password_ui._render")
    def test_passes_token(self, mock_render: MagicMock) -> None:
        asyncio.run(reset_password_page(_req(), token="abc"))
        ctx = mock_render.call_args[0][2]
        assert ctx["token"] == "abc"


class TestResetPasswordSubmit:
    """POST /ui/password/reset-verify."""

    @patch("shomer.routes.password_ui.AuthService")
    @patch("shomer.routes.password_ui._render")
    def test_success(self, mock_render: MagicMock, mock_cls: MagicMock) -> None:
        mock_cls.return_value = AsyncMock()
        token = str(uuid.uuid4())
        asyncio.run(reset_password_submit(_req(), AsyncMock(), token, "newpw123456"))
        ctx = mock_render.call_args[0][2]
        assert "success" in ctx

    @patch("shomer.routes.password_ui._render")
    def test_malformed_token(self, mock_render: MagicMock) -> None:
        asyncio.run(reset_password_submit(_req(), AsyncMock(), "bad", "newpw123456"))
        ctx = mock_render.call_args[0][2]
        assert "error" in ctx

    @patch("shomer.routes.password_ui.AuthService")
    @patch("shomer.routes.password_ui._render")
    def test_invalid_token(self, mock_render: MagicMock, mock_cls: MagicMock) -> None:
        mock_svc = AsyncMock()
        mock_svc.verify_password_reset.side_effect = InvalidResetTokenError()
        mock_cls.return_value = mock_svc
        token = str(uuid.uuid4())
        asyncio.run(reset_password_submit(_req(), AsyncMock(), token, "newpw123456"))
        ctx = mock_render.call_args[0][2]
        assert "error" in ctx


class TestChangePasswordPage:
    """GET /ui/password/change."""

    @patch("shomer.routes.password_ui._render")
    def test_renders_page(self, mock_render: MagicMock) -> None:
        asyncio.run(change_password_page(_req()))
        mock_render.assert_called_once()


class TestChangePasswordSubmit:
    """POST /ui/password/change."""

    @patch("shomer.routes.password_ui._render")
    def test_no_session(self, mock_render: MagicMock) -> None:
        asyncio.run(change_password_submit(_req(), AsyncMock(), "old", "new123456"))
        ctx = mock_render.call_args[0][2]
        assert "Authentication required" in ctx["error"]

    @patch("shomer.routes.password_ui.SessionService")
    @patch("shomer.routes.password_ui._render")
    def test_expired_session(self, mock_render: MagicMock, mock_cls: MagicMock) -> None:
        mock_svc = AsyncMock()
        mock_svc.validate.return_value = None
        mock_cls.return_value = mock_svc
        asyncio.run(
            change_password_submit(
                _req({"session_id": "tok"}), AsyncMock(), "old", "new123456"
            )
        )
        ctx = mock_render.call_args[0][2]
        assert "expired" in ctx["error"].lower()

    @patch("shomer.routes.password_ui.AuthService")
    @patch("shomer.routes.password_ui.SessionService")
    @patch("shomer.routes.password_ui._render")
    def test_success(
        self,
        mock_render: MagicMock,
        mock_sess_cls: MagicMock,
        mock_auth_cls: MagicMock,
    ) -> None:
        mock_session = MagicMock(user_id=uuid.uuid4())
        mock_sess = AsyncMock()
        mock_sess.validate.return_value = mock_session
        mock_sess_cls.return_value = mock_sess
        mock_auth_cls.return_value = AsyncMock()
        asyncio.run(
            change_password_submit(
                _req({"session_id": "tok"}), AsyncMock(), "old", "new123456"
            )
        )
        ctx = mock_render.call_args[0][2]
        assert "success" in ctx

    @patch("shomer.routes.password_ui.AuthService")
    @patch("shomer.routes.password_ui.SessionService")
    @patch("shomer.routes.password_ui._render")
    def test_wrong_password(
        self,
        mock_render: MagicMock,
        mock_sess_cls: MagicMock,
        mock_auth_cls: MagicMock,
    ) -> None:
        mock_session = MagicMock(user_id=uuid.uuid4())
        mock_sess = AsyncMock()
        mock_sess.validate.return_value = mock_session
        mock_sess_cls.return_value = mock_sess
        mock_auth = AsyncMock()
        mock_auth.change_password.side_effect = InvalidCredentialsError()
        mock_auth_cls.return_value = mock_auth
        asyncio.run(
            change_password_submit(
                _req({"session_id": "tok"}), AsyncMock(), "wrong", "new123456"
            )
        )
        ctx = mock_render.call_args[0][2]
        assert "error" in ctx

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Pure unit tests for auth UI route handlers."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from shomer.routes.auth_ui import (
    login_page,
    login_submit,
    register_page,
    register_submit,
    verify_page,
    verify_resend,
    verify_submit,
)
from shomer.services.auth_service import (
    EmailNotFoundError,
    EmailNotVerifiedError,
    InvalidCodeError,
    InvalidCredentialsError,
    RateLimitError,
)


def _req() -> MagicMock:
    r = MagicMock()
    r.headers = MagicMock()
    r.headers.get = MagicMock(return_value="Agent")
    r.client = MagicMock()
    r.client.host = "127.0.0.1"
    return r


class TestRenderHelper:
    """Tests for _templates() and _render() helpers."""

    @patch("shomer.routes.auth_ui._templates")
    def test_render_calls_template_response(self, mock_tpl: MagicMock) -> None:
        from shomer.routes.auth_ui import _render

        mock_tpl.return_value.TemplateResponse.return_value = "resp"
        result = _render(MagicMock(), "test.html", {"k": "v"})
        assert result == "resp"

    def test_templates_returns_jinja(self) -> None:
        from shomer.routes.auth_ui import _templates

        result = _templates()
        assert result is not None


class TestRegisterPage:
    """GET /ui/register."""

    @patch("shomer.routes.auth_ui._render")
    def test_renders_register(self, mock_render: MagicMock) -> None:
        asyncio.run(register_page(_req()))
        mock_render.assert_called_once()
        assert "register" in mock_render.call_args[0][1]


class TestRegisterSubmit:
    """POST /ui/register."""

    @patch("shomer.routes.auth_ui.send_email_task")
    @patch("shomer.routes.auth_ui.AuthService")
    @patch("shomer.routes.auth_ui._render")
    def test_submit_renders_verify(
        self, mock_render: MagicMock, mock_cls: MagicMock, mock_task: MagicMock
    ) -> None:
        mock_svc = AsyncMock()
        mock_svc.register.return_value = (MagicMock(), "123456")
        mock_cls.return_value = mock_svc
        asyncio.run(register_submit(_req(), AsyncMock(), "a@b.com", "pw123456", ""))
        mock_task.delay.assert_called_once()
        assert "verify" in mock_render.call_args[0][1]


class TestVerifyPage:
    """GET /ui/verify."""

    @patch("shomer.routes.auth_ui._render")
    def test_renders_verify(self, mock_render: MagicMock) -> None:
        asyncio.run(verify_page(_req()))
        mock_render.assert_called_once()


class TestVerifySubmit:
    """POST /ui/verify."""

    @patch("shomer.routes.auth_ui.AuthService")
    @patch("shomer.routes.auth_ui._render")
    def test_success_renders_login(
        self, mock_render: MagicMock, mock_cls: MagicMock
    ) -> None:
        mock_cls.return_value = AsyncMock()
        asyncio.run(verify_submit(_req(), AsyncMock(), "a@b.com", "123456"))
        assert "login" in mock_render.call_args[0][1]

    @patch("shomer.routes.auth_ui.AuthService")
    @patch("shomer.routes.auth_ui._render")
    def test_invalid_code_shows_error(
        self, mock_render: MagicMock, mock_cls: MagicMock
    ) -> None:
        mock_svc = AsyncMock()
        mock_svc.verify_email.side_effect = InvalidCodeError()
        mock_cls.return_value = mock_svc
        asyncio.run(verify_submit(_req(), AsyncMock(), "a@b.com", "000000"))
        ctx = mock_render.call_args[0][2]
        assert "error" in ctx


class TestVerifyResend:
    """POST /ui/verify/resend."""

    @patch("shomer.routes.auth_ui.send_email_task")
    @patch("shomer.routes.auth_ui.AuthService")
    @patch("shomer.routes.auth_ui._render")
    def test_success(
        self, mock_render: MagicMock, mock_cls: MagicMock, mock_task: MagicMock
    ) -> None:
        mock_svc = AsyncMock()
        mock_svc.resend_code.return_value = "654321"
        mock_cls.return_value = mock_svc
        asyncio.run(verify_resend(_req(), AsyncMock(), "a@b.com"))
        mock_task.delay.assert_called_once()
        ctx = mock_render.call_args[0][2]
        assert "success" in ctx

    @patch("shomer.routes.auth_ui.AuthService")
    @patch("shomer.routes.auth_ui._render")
    def test_not_found(self, mock_render: MagicMock, mock_cls: MagicMock) -> None:
        mock_svc = AsyncMock()
        mock_svc.resend_code.side_effect = EmailNotFoundError()
        mock_cls.return_value = mock_svc
        asyncio.run(verify_resend(_req(), AsyncMock(), "x@b.com"))
        ctx = mock_render.call_args[0][2]
        assert "error" in ctx

    @patch("shomer.routes.auth_ui.AuthService")
    @patch("shomer.routes.auth_ui._render")
    def test_rate_limited(self, mock_render: MagicMock, mock_cls: MagicMock) -> None:
        mock_svc = AsyncMock()
        mock_svc.resend_code.side_effect = RateLimitError()
        mock_cls.return_value = mock_svc
        asyncio.run(verify_resend(_req(), AsyncMock(), "a@b.com"))
        ctx = mock_render.call_args[0][2]
        assert "error" in ctx


class TestLoginPage:
    """GET /ui/login."""

    @patch("shomer.routes.auth_ui._render")
    def test_renders_login(self, mock_render: MagicMock) -> None:
        asyncio.run(login_page(_req()))
        mock_render.assert_called_once()

    @patch("shomer.routes.auth_ui._render")
    def test_passes_next_param(self, mock_render: MagicMock) -> None:
        asyncio.run(login_page(_req(), next="/dashboard"))
        ctx = mock_render.call_args[0][2]
        assert ctx["next"] == "/dashboard"


class TestLoginSubmit:
    """POST /ui/login."""

    @patch("shomer.routes.auth_ui.AuthService")
    def test_success_redirects(self, mock_cls: MagicMock) -> None:
        mock_svc = AsyncMock()
        mock_svc.login.return_value = (MagicMock(), MagicMock(csrf_token="c"), "tok")
        mock_cls.return_value = mock_svc
        resp = asyncio.run(login_submit(_req(), AsyncMock(), "a@b.com", "pw", ""))
        assert resp.status_code == 303

    @patch("shomer.routes.auth_ui.AuthService")
    @patch("shomer.routes.auth_ui._render")
    def test_invalid_credentials(
        self, mock_render: MagicMock, mock_cls: MagicMock
    ) -> None:
        mock_svc = AsyncMock()
        mock_svc.login.side_effect = InvalidCredentialsError()
        mock_cls.return_value = mock_svc
        asyncio.run(login_submit(_req(), AsyncMock(), "a@b.com", "wrong", ""))
        ctx = mock_render.call_args[0][2]
        assert "error" in ctx

    @patch("shomer.routes.auth_ui.AuthService")
    @patch("shomer.routes.auth_ui._render")
    def test_email_not_verified(
        self, mock_render: MagicMock, mock_cls: MagicMock
    ) -> None:
        mock_svc = AsyncMock()
        mock_svc.login.side_effect = EmailNotVerifiedError()
        mock_cls.return_value = mock_svc
        asyncio.run(login_submit(_req(), AsyncMock(), "a@b.com", "pw", ""))
        ctx = mock_render.call_args[0][2]
        assert "not verified" in ctx["error"]

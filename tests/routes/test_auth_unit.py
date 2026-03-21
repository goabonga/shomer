# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Pure unit tests for auth route handlers — direct function calls with mocks."""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from shomer.routes.auth import (
    _build_mfa_token,
    login,
    logout,
    password_change,
    password_reset,
    password_reset_verify,
    register,
    resend,
    verify,
    verify_mfa_token,
)
from shomer.services.auth_service import (
    EmailNotFoundError,
    EmailNotVerifiedError,
    InvalidCodeError,
    InvalidCredentialsError,
    InvalidResetTokenError,
    RateLimitError,
)


def _mock_db() -> AsyncMock:
    return AsyncMock()


def _mock_request(cookies: dict[str, str] | None = None) -> MagicMock:
    cookie_data = cookies or {}
    req = MagicMock()
    req.cookies = MagicMock()
    req.cookies.get = lambda k, d=None: cookie_data.get(k, d)
    req.headers = MagicMock()
    req.headers.get = MagicMock(return_value="TestAgent")
    req.client = MagicMock()
    req.client.host = "127.0.0.1"
    return req


class TestRegisterRoute:
    """Unit tests for POST /auth/register."""

    @patch("shomer.routes.auth.send_email_task")
    @patch("shomer.routes.auth.AuthService")
    def test_register_success(self, mock_cls: MagicMock, mock_task: MagicMock) -> None:
        async def _run() -> None:
            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()
            mock_svc = AsyncMock()
            mock_svc.register.return_value = (mock_user, "123456")
            mock_cls.return_value = mock_svc
            body = MagicMock(email="a@b.com", password="pw", username=None)
            result = await register(body, _mock_db())
            assert "Registration successful" in result.message
            assert result.user_id == str(mock_user.id)
            mock_task.delay.assert_called_once()

        asyncio.run(_run())

    @patch("shomer.routes.auth.send_email_task")
    @patch("shomer.routes.auth.AuthService")
    def test_register_duplicate_returns_empty_id(
        self, mock_cls: MagicMock, mock_task: MagicMock
    ) -> None:
        async def _run() -> None:
            mock_svc = AsyncMock()
            mock_svc.register.return_value = (None, "")
            mock_cls.return_value = mock_svc
            body = MagicMock(email="dupe@b.com", password="pw", username=None)
            result = await register(body, _mock_db())
            assert result.user_id == ""

        asyncio.run(_run())


class TestVerifyRoute:
    """Unit tests for POST /auth/verify."""

    @patch("shomer.routes.auth.AuthService")
    def test_verify_success(self, mock_cls: MagicMock) -> None:
        async def _run() -> None:
            mock_svc = AsyncMock()
            mock_cls.return_value = mock_svc
            body = MagicMock(email="a@b.com", code="123456")
            result = await verify(body, _mock_db())
            assert result.message == "Email verified successfully"

        asyncio.run(_run())

    @patch("shomer.routes.auth.AuthService")
    def test_verify_invalid_code(self, mock_cls: MagicMock) -> None:
        async def _run() -> None:
            mock_svc = AsyncMock()
            mock_svc.verify_email.side_effect = InvalidCodeError()
            mock_cls.return_value = mock_svc
            body = MagicMock(email="a@b.com", code="000000")
            with pytest.raises(HTTPException) as exc_info:
                await verify(body, _mock_db())
            assert exc_info.value.status_code == 400

        asyncio.run(_run())


class TestResendRoute:
    """Unit tests for POST /auth/verify/resend."""

    @patch("shomer.routes.auth.send_email_task")
    @patch("shomer.routes.auth.AuthService")
    def test_resend_success(self, mock_cls: MagicMock, mock_task: MagicMock) -> None:
        async def _run() -> None:
            mock_svc = AsyncMock()
            mock_svc.resend_code.return_value = "654321"
            mock_cls.return_value = mock_svc
            body = MagicMock(email="a@b.com")
            result = await resend(body, _mock_db())
            assert "code sent" in result.message.lower()
            mock_task.delay.assert_called_once()

        asyncio.run(_run())

    @patch("shomer.routes.auth.AuthService")
    def test_resend_not_found(self, mock_cls: MagicMock) -> None:
        async def _run() -> None:
            mock_svc = AsyncMock()
            mock_svc.resend_code.side_effect = EmailNotFoundError()
            mock_cls.return_value = mock_svc
            body = MagicMock(email="x@b.com")
            with pytest.raises(HTTPException) as exc_info:
                await resend(body, _mock_db())
            assert exc_info.value.status_code == 404

        asyncio.run(_run())

    @patch("shomer.routes.auth.AuthService")
    def test_resend_rate_limited(self, mock_cls: MagicMock) -> None:
        async def _run() -> None:
            mock_svc = AsyncMock()
            mock_svc.resend_code.side_effect = RateLimitError()
            mock_cls.return_value = mock_svc
            body = MagicMock(email="a@b.com")
            with pytest.raises(HTTPException) as exc_info:
                await resend(body, _mock_db())
            assert exc_info.value.status_code == 429

        asyncio.run(_run())


class TestLoginRoute:
    """Unit tests for POST /auth/login."""

    @patch("shomer.routes.auth.AuthService")
    def test_login_success(self, mock_cls: MagicMock) -> None:
        async def _run() -> None:
            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()
            mock_session = MagicMock()
            mock_session.csrf_token = "csrf123"
            mock_svc = AsyncMock()
            mock_svc.login.return_value = (mock_user, mock_session, "raw-token")
            mock_cls.return_value = mock_svc
            body = MagicMock(email="a@b.com", password="pw")
            # Mock MFA query to return no MFA
            mock_mfa_result = MagicMock()
            mock_mfa_result.scalar_one_or_none.return_value = None
            db = AsyncMock()
            db.execute.return_value = mock_mfa_result
            resp = await login(body, _mock_request(), db)
            assert resp.status_code == 200

        asyncio.run(_run())

    @patch("shomer.routes.auth.AuthService")
    def test_login_invalid_credentials(self, mock_cls: MagicMock) -> None:
        async def _run() -> None:
            mock_svc = AsyncMock()
            mock_svc.login.side_effect = InvalidCredentialsError()
            mock_cls.return_value = mock_svc
            body = MagicMock(email="a@b.com", password="wrong")
            with pytest.raises(HTTPException) as exc_info:
                await login(body, _mock_request(), _mock_db())
            assert exc_info.value.status_code == 401

        asyncio.run(_run())

    @patch("shomer.routes.auth.AuthService")
    def test_login_email_not_verified(self, mock_cls: MagicMock) -> None:
        async def _run() -> None:
            mock_svc = AsyncMock()
            mock_svc.login.side_effect = EmailNotVerifiedError()
            mock_cls.return_value = mock_svc
            body = MagicMock(email="a@b.com", password="pw")
            with pytest.raises(HTTPException) as exc_info:
                await login(body, _mock_request(), _mock_db())
            assert exc_info.value.status_code == 403

        asyncio.run(_run())


class TestLogoutRoute:
    """Unit tests for POST /auth/logout."""

    @patch("shomer.routes.auth.SessionService")
    def test_logout_single(self, mock_cls: MagicMock) -> None:
        async def _run() -> None:
            mock_session = MagicMock()
            mock_session.id = uuid.uuid4()
            mock_session.user_id = uuid.uuid4()
            mock_svc = AsyncMock()
            mock_svc.validate.return_value = mock_session
            mock_cls.return_value = mock_svc
            req = _mock_request({"session_id": "token"})
            resp = await logout(req, _mock_db(), None)
            mock_svc.delete.assert_awaited_once_with(mock_session.id)
            assert resp.status_code == 200

        asyncio.run(_run())

    @patch("shomer.routes.auth.SessionService")
    def test_logout_all(self, mock_cls: MagicMock) -> None:
        async def _run() -> None:
            mock_session = MagicMock()
            mock_session.user_id = uuid.uuid4()
            mock_svc = AsyncMock()
            mock_svc.validate.return_value = mock_session
            mock_cls.return_value = mock_svc
            req = _mock_request({"session_id": "token"})
            body = MagicMock(logout_all=True)
            resp = await logout(req, _mock_db(), body)
            mock_svc.delete_all_for_user.assert_awaited_once()
            assert resp.status_code == 200

        asyncio.run(_run())


class TestPasswordResetRoute:
    """Unit tests for POST /auth/password/reset."""

    @patch("shomer.routes.auth.send_email_task")
    @patch("shomer.routes.auth.AuthService")
    def test_reset_dispatches_task(
        self, mock_cls: MagicMock, mock_task: MagicMock
    ) -> None:
        async def _run() -> None:
            mock_svc = AsyncMock()
            mock_svc.request_password_reset.return_value = uuid.uuid4()
            mock_cls.return_value = mock_svc
            body = MagicMock(email="a@b.com")
            result = await password_reset(body, _mock_db())
            assert "reset link" in result.message.lower()
            mock_task.delay.assert_called_once()

        asyncio.run(_run())

    @patch("shomer.routes.auth.send_email_task")
    @patch("shomer.routes.auth.AuthService")
    def test_reset_unknown_email(
        self, mock_cls: MagicMock, mock_task: MagicMock
    ) -> None:
        async def _run() -> None:
            mock_svc = AsyncMock()
            mock_svc.request_password_reset.return_value = None
            mock_cls.return_value = mock_svc
            body = MagicMock(email="nope@b.com")
            result = await password_reset(body, _mock_db())
            assert "reset link" in result.message.lower()

        asyncio.run(_run())


class TestPasswordResetVerifyRoute:
    """Unit tests for POST /auth/password/reset-verify."""

    @patch("shomer.routes.auth.AuthService")
    def test_reset_verify_success(self, mock_cls: MagicMock) -> None:
        async def _run() -> None:
            mock_svc = AsyncMock()
            mock_cls.return_value = mock_svc
            body = MagicMock(token=str(uuid.uuid4()), new_password="newsecurepassword1")
            result = await password_reset_verify(body, _mock_db())
            assert "reset" in result.message.lower()

        asyncio.run(_run())

    def test_reset_verify_malformed_token(self) -> None:
        async def _run() -> None:
            body = MagicMock(token="not-a-uuid", new_password="newsecurepassword1")
            with pytest.raises(HTTPException) as exc_info:
                await password_reset_verify(body, _mock_db())
            assert exc_info.value.status_code == 400

        asyncio.run(_run())

    @patch("shomer.routes.auth.AuthService")
    def test_reset_verify_invalid_token(self, mock_cls: MagicMock) -> None:
        async def _run() -> None:
            mock_svc = AsyncMock()
            mock_svc.verify_password_reset.side_effect = InvalidResetTokenError()
            mock_cls.return_value = mock_svc
            body = MagicMock(token=str(uuid.uuid4()), new_password="newsecurepassword1")
            with pytest.raises(HTTPException) as exc_info:
                await password_reset_verify(body, _mock_db())
            assert exc_info.value.status_code == 400

        asyncio.run(_run())


class TestPasswordChangeRoute:
    """Unit tests for POST /auth/password/change."""

    @patch("shomer.routes.auth.AuthService")
    @patch("shomer.routes.auth.SessionService")
    def test_change_success(
        self, mock_sess_cls: MagicMock, mock_auth_cls: MagicMock
    ) -> None:
        async def _run() -> None:
            mock_session = MagicMock()
            mock_session.user_id = uuid.uuid4()
            mock_sess = AsyncMock()
            mock_sess.validate.return_value = mock_session
            mock_sess_cls.return_value = mock_sess
            mock_auth = AsyncMock()
            mock_auth_cls.return_value = mock_auth
            req = _mock_request({"session_id": "tok"})
            body = MagicMock(current_password="old", new_password="newsecurepassword1")
            result = await password_change(body, req, _mock_db())
            assert "changed" in result.message.lower()

        asyncio.run(_run())

    def test_change_no_session(self) -> None:
        async def _run() -> None:
            req = _mock_request({})
            body = MagicMock(current_password="old", new_password="newsecurepassword1")
            with pytest.raises(HTTPException) as exc_info:
                await password_change(body, req, _mock_db())
            assert exc_info.value.status_code == 401

        asyncio.run(_run())

    @patch("shomer.routes.auth.SessionService")
    def test_change_invalid_session(self, mock_cls: MagicMock) -> None:
        async def _run() -> None:
            mock_svc = AsyncMock()
            mock_svc.validate.return_value = None
            mock_cls.return_value = mock_svc
            req = _mock_request({"session_id": "bad"})
            body = MagicMock(current_password="old", new_password="newsecurepassword1")
            with pytest.raises(HTTPException) as exc_info:
                await password_change(body, req, _mock_db())
            assert exc_info.value.status_code == 401

        asyncio.run(_run())

    @patch("shomer.routes.auth.AuthService")
    @patch("shomer.routes.auth.SessionService")
    def test_change_wrong_current_password(
        self, mock_sess_cls: MagicMock, mock_auth_cls: MagicMock
    ) -> None:
        async def _run() -> None:
            mock_session = MagicMock()
            mock_session.user_id = uuid.uuid4()
            mock_sess = AsyncMock()
            mock_sess.validate.return_value = mock_session
            mock_sess_cls.return_value = mock_sess
            mock_auth = AsyncMock()
            mock_auth.change_password.side_effect = InvalidCredentialsError()
            mock_auth_cls.return_value = mock_auth
            req = _mock_request({"session_id": "tok"})
            body = MagicMock(
                current_password="wrong", new_password="newsecurepassword1"
            )
            with pytest.raises(HTTPException) as exc_info:
                await password_change(body, req, _mock_db())
            assert exc_info.value.status_code == 401

        asyncio.run(_run())


class TestMFALoginChallenge:
    """Unit tests for MFA two-step login challenge."""

    def test_login_with_mfa_returns_mfa_required(self) -> None:
        """Login with MFA-enabled user returns mfa_token."""

        async def _run() -> None:
            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()
            mock_session = MagicMock()
            mock_session.id = uuid.uuid4()
            mock_session.csrf_token = "csrf"

            mock_mfa = MagicMock()
            mock_mfa.is_enabled = True
            mock_mfa.methods = ["totp", "backup"]

            mock_mfa_result = MagicMock()
            mock_mfa_result.scalar_one_or_none.return_value = mock_mfa

            with (
                patch("shomer.routes.auth.AuthService") as mock_auth_cls,
                patch("shomer.routes.auth.SessionService") as mock_sess_cls,
            ):
                mock_auth = AsyncMock()
                mock_auth.login.return_value = (mock_user, mock_session, "tok")
                mock_auth_cls.return_value = mock_auth

                mock_sess_svc = AsyncMock()
                mock_sess_cls.return_value = mock_sess_svc

                body = MagicMock(email="u@b.com", password="pw")
                req = MagicMock()
                req.headers.get.return_value = "ua"
                req.client.host = "127.0.0.1"

                db = AsyncMock()
                db.execute.return_value = mock_mfa_result

                resp = await login(body, req, db)
                import json

                data = json.loads(bytes(resp.body))
                assert data["mfa_required"] is True
                assert "mfa_token" in data
                assert "totp" in data["methods"]
                mock_sess_svc.delete.assert_awaited_once_with(mock_session.id)

        asyncio.run(_run())

    def test_login_without_mfa_returns_session(self) -> None:
        """Login without MFA returns normal session."""

        async def _run() -> None:
            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()
            mock_session = MagicMock()
            mock_session.csrf_token = "csrf"

            mock_mfa_result = MagicMock()
            mock_mfa_result.scalar_one_or_none.return_value = None

            with patch("shomer.routes.auth.AuthService") as mock_auth_cls:
                mock_auth = AsyncMock()
                mock_auth.login.return_value = (mock_user, mock_session, "tok")
                mock_auth_cls.return_value = mock_auth

                body = MagicMock(email="u@b.com", password="pw")
                req = MagicMock()
                req.headers.get.return_value = "ua"
                req.client.host = "127.0.0.1"

                db = AsyncMock()
                db.execute.return_value = mock_mfa_result

                resp = await login(body, req, db)
                import json

                data = json.loads(bytes(resp.body))
                assert data["message"] == "Login successful"
                assert "mfa_required" not in data

        asyncio.run(_run())


class TestMFATokenHelpers:
    """Unit tests for MFA token build/verify."""

    def test_build_and_verify_roundtrip(self) -> None:
        settings = MagicMock()
        settings.jwk_encryption_key = "test-key"
        token = _build_mfa_token("user-123", settings)
        result = verify_mfa_token(token, settings)
        assert result == "user-123"

    def test_verify_expired_token(self) -> None:
        import time

        import jwt as pyjwt

        payload = {
            "sub": "user-123",
            "purpose": "mfa_challenge",
            "iat": int(time.time()) - 600,
            "exp": int(time.time()) - 300,
        }
        token = pyjwt.encode(payload, "test-key", algorithm="HS256")
        settings = MagicMock()
        settings.jwk_encryption_key = "test-key"
        assert verify_mfa_token(token, settings) is None

    def test_verify_wrong_purpose(self) -> None:
        import time

        import jwt as pyjwt

        payload = {
            "sub": "user-123",
            "purpose": "wrong",
            "iat": int(time.time()),
            "exp": int(time.time()) + 300,
        }
        token = pyjwt.encode(payload, "test-key", algorithm="HS256")
        settings = MagicMock()
        settings.jwk_encryption_key = "test-key"
        assert verify_mfa_token(token, settings) is None

    def test_verify_invalid_token(self) -> None:
        settings = MagicMock()
        settings.jwk_encryption_key = "test-key"
        assert verify_mfa_token("garbage", settings) is None

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Pure unit tests for MFA UI route handlers."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from shomer.routes.mfa_ui import (
    mfa_challenge_page,
    mfa_challenge_submit,
    mfa_setup_page,
    mfa_setup_submit,
)


class TestMFASetupPage:
    """Unit tests for GET /ui/mfa/setup."""

    def test_unauthenticated_redirects_to_login(self) -> None:
        async def _run() -> None:
            with patch(
                "shomer.routes.mfa_ui._get_session_user_id",
                new_callable=AsyncMock,
                return_value=None,
            ):
                req = MagicMock()
                resp = await mfa_setup_page(req, AsyncMock())
                assert resp.status_code == 302
                assert "/ui/login" in resp.headers["location"]

        asyncio.run(_run())

    def test_authenticated_renders_page(self) -> None:
        async def _run() -> None:
            import uuid

            with (
                patch(
                    "shomer.routes.mfa_ui._get_session_user_id",
                    new_callable=AsyncMock,
                    return_value=uuid.uuid4(),
                ),
                patch("shomer.app.templates") as mock_tpl,
            ):
                mock_tpl.TemplateResponse.return_value = MagicMock()
                req = MagicMock()
                await mfa_setup_page(req, AsyncMock())
                mock_tpl.TemplateResponse.assert_called_once()

        asyncio.run(_run())


class TestMFASetupSubmit:
    """Unit tests for POST /ui/mfa/setup."""

    def test_unauthenticated_redirects(self) -> None:
        async def _run() -> None:
            with patch(
                "shomer.routes.mfa_ui._get_session_user_id",
                new_callable=AsyncMock,
                return_value=None,
            ):
                req = MagicMock()
                resp = await mfa_setup_submit(req, AsyncMock(), MagicMock())
                assert resp.status_code == 302

        asyncio.run(_run())

    def test_generate_step_returns_secret(self) -> None:
        async def _run() -> None:
            import base64
            import uuid

            mock_email = MagicMock()
            mock_email.email = "u@b.com"
            mock_email_result = MagicMock()
            mock_email_result.scalar_one_or_none.return_value = mock_email

            mock_mfa_result = MagicMock()
            mock_mfa_result.scalar_one_or_none.return_value = None

            db = AsyncMock()
            db.execute.side_effect = [mock_email_result, mock_mfa_result]

            config = MagicMock()
            config.jwk_encryption_key = base64.b64encode(b"a" * 32).decode()

            with (
                patch(
                    "shomer.routes.mfa_ui._get_session_user_id",
                    new_callable=AsyncMock,
                    return_value=uuid.uuid4(),
                ),
                patch("shomer.app.templates") as mock_tpl,
            ):
                mock_tpl.TemplateResponse.return_value = MagicMock()
                req = MagicMock()
                await mfa_setup_submit(req, db, config, step="generate")
                call_args = mock_tpl.TemplateResponse.call_args
                ctx = call_args[0][2] if len(call_args[0]) > 2 else call_args[1]
                assert "secret" in ctx
                assert "provisioning_uri" in ctx
                assert ctx["provisioning_uri"].startswith("otpauth://totp/")

        asyncio.run(_run())


class TestMFAChallengePage:
    """Unit tests for GET /ui/mfa/challenge."""

    def test_no_token_redirects_to_login(self) -> None:
        async def _run() -> None:
            req = MagicMock()
            resp = await mfa_challenge_page(req, mfa_token="")
            assert resp.status_code == 302
            assert "/ui/login" in resp.headers["location"]

        asyncio.run(_run())

    def test_with_token_renders_page(self) -> None:
        async def _run() -> None:
            with patch("shomer.app.templates") as mock_tpl:
                mock_tpl.TemplateResponse.return_value = MagicMock()
                req = MagicMock()
                await mfa_challenge_page(req, mfa_token="tok", method="totp")
                mock_tpl.TemplateResponse.assert_called_once()
                call_args = mock_tpl.TemplateResponse.call_args
                ctx = call_args[0][2] if len(call_args[0]) > 2 else call_args[1]
                assert ctx["mfa_token"] == "tok"
                assert ctx["method"] == "totp"

        asyncio.run(_run())


class TestMFAChallengeSubmit:
    """Unit tests for POST /ui/mfa/challenge."""

    def test_invalid_token_renders_error(self) -> None:
        async def _run() -> None:
            with (
                patch("shomer.routes.auth.verify_mfa_token", return_value=None),
                patch("shomer.app.templates") as mock_tpl,
            ):
                mock_tpl.TemplateResponse.return_value = MagicMock()
                req = MagicMock()
                await mfa_challenge_submit(
                    req, AsyncMock(), MagicMock(), "bad-token", "123456", "totp"
                )
                call_args = mock_tpl.TemplateResponse.call_args
                ctx = call_args[0][2] if len(call_args[0]) > 2 else call_args[1]
                assert "expired" in ctx.get("error", "").lower()

        asyncio.run(_run())

    def test_valid_totp_creates_session_and_redirects(self) -> None:
        async def _run() -> None:
            import uuid

            mock_mfa = MagicMock()
            mock_mfa.is_enabled = True
            mock_mfa.totp_secret_encrypted = "enc"
            mock_mfa_result = MagicMock()
            mock_mfa_result.scalar_one_or_none.return_value = mock_mfa

            db = AsyncMock()
            db.execute.return_value = mock_mfa_result

            mock_session = MagicMock()
            mock_session.csrf_token = "csrf"

            uid = str(uuid.uuid4())

            mock_policy = MagicMock()
            mock_policy.httponly = True
            mock_policy.secure = False
            mock_policy.samesite = "lax"
            mock_policy.domain = None

            with (
                patch("shomer.routes.auth.verify_mfa_token", return_value=uid),
                patch("shomer.routes.mfa_ui.MFAService") as svc_cls,
                patch("shomer.routes.mfa_ui.SessionService") as sess_cls,
                patch(
                    "shomer.middleware.cookies.get_cookie_policy",
                    return_value=mock_policy,
                ),
            ):
                mock_svc = MagicMock()
                mock_svc.decrypt_totp_secret.return_value = "SECRET"
                svc_cls.return_value = mock_svc
                svc_cls.verify_totp_code.return_value = True

                mock_sess_svc = AsyncMock()
                mock_sess_svc.create.return_value = (mock_session, "raw-tok")
                sess_cls.return_value = mock_sess_svc

                config = MagicMock()
                req = MagicMock()
                req.headers.get.return_value = "ua"
                req.client.host = "127.0.0.1"
                req.cookies.get.return_value = None

                resp = await mfa_challenge_submit(
                    req, db, config, "valid-token", "123456", "totp"
                )
                assert resp.status_code == 302

        asyncio.run(_run())

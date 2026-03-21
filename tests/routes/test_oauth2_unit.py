# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Pure unit tests for oauth2 route handlers — direct function calls with mocks."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from shomer.routes.oauth2 import (
    _FRIENDLY_ERROR_MESSAGES,
    _handle_client_credentials,
    _handle_password_grant,
    _render_oauth2_error,
    authorize,
    authorize_consent,
)
from shomer.services.authorize_service import AuthorizeError
from shomer.services.oauth2_client_service import InvalidClientError
from shomer.services.token_service import TokenError, TokenResponse


def _mock_client(
    *,
    client_type: str = "confidential",
    grant_types: list[str] | None = None,
    scopes: list[str] | None = None,
) -> MagicMock:
    c = MagicMock()
    c.client_id = "test-client"
    c.client_type = MagicMock()
    c.client_type.value = client_type
    c.grant_types = grant_types or []
    c.scopes = scopes or []
    # Make the enum comparison work
    from shomer.models.oauth2_client import ClientType

    if client_type == "public":
        c.client_type = ClientType.PUBLIC
    else:
        c.client_type = ClientType.CONFIDENTIAL
    return c


class TestHandleClientCredentials:
    """Unit tests for _handle_client_credentials."""

    def test_public_client_rejected(self) -> None:
        async def _run() -> None:
            client = _mock_client(client_type="public")
            svc = AsyncMock()
            resp = await _handle_client_credentials(svc, client, "")
            assert resp.status_code == 400
            assert b"unauthorized_client" in resp.body

        asyncio.run(_run())

    def test_grant_not_allowed(self) -> None:
        async def _run() -> None:
            client = _mock_client(grant_types=["authorization_code"])
            svc = AsyncMock()
            resp = await _handle_client_credentials(svc, client, "")
            assert resp.status_code == 400
            assert b"not authorized" in resp.body

        asyncio.run(_run())

    def test_success(self) -> None:
        async def _run() -> None:
            client = _mock_client(grant_types=["client_credentials"], scopes=["read"])
            svc = AsyncMock()
            svc.issue_client_credentials.return_value = TokenResponse(
                access_token="tok"
            )
            resp = await _handle_client_credentials(svc, client, "read")
            assert resp.status_code == 200
            assert b"tok" in resp.body

        asyncio.run(_run())

    def test_token_error(self) -> None:
        async def _run() -> None:
            client = _mock_client(grant_types=["client_credentials"], scopes=["read"])
            svc = AsyncMock()
            svc.issue_client_credentials.side_effect = TokenError(
                "invalid_scope", "bad"
            )
            resp = await _handle_client_credentials(svc, client, "bad")
            assert resp.status_code == 400
            assert b"invalid_scope" in resp.body

        asyncio.run(_run())


class TestHandlePasswordGrant:
    """Unit tests for _handle_password_grant."""

    def test_grant_not_allowed(self) -> None:
        async def _run() -> None:
            client = _mock_client(grant_types=["authorization_code"])
            svc = AsyncMock()
            resp = await _handle_password_grant(svc, client, "u", "p", "")
            assert resp.status_code == 400
            assert b"not authorized" in resp.body

        asyncio.run(_run())

    def test_missing_username(self) -> None:
        async def _run() -> None:
            client = _mock_client(grant_types=["password"])
            svc = AsyncMock()
            resp = await _handle_password_grant(svc, client, "", "p", "")
            assert resp.status_code == 400
            assert b"required" in resp.body

        asyncio.run(_run())

    def test_missing_password(self) -> None:
        async def _run() -> None:
            client = _mock_client(grant_types=["password"])
            svc = AsyncMock()
            resp = await _handle_password_grant(svc, client, "u", "", "")
            assert resp.status_code == 400
            assert b"required" in resp.body

        asyncio.run(_run())

    def test_success(self) -> None:
        async def _run() -> None:
            client = _mock_client(grant_types=["password"])
            svc = AsyncMock()
            svc.issue_password_grant.return_value = TokenResponse(
                access_token="tok", refresh_token="ref"
            )
            resp = await _handle_password_grant(svc, client, "u@b.com", "pw", "")
            assert resp.status_code == 200
            assert b"tok" in resp.body

        asyncio.run(_run())

    def test_token_error(self) -> None:
        async def _run() -> None:
            client = _mock_client(grant_types=["password"])
            svc = AsyncMock()
            svc.issue_password_grant.side_effect = TokenError(
                "invalid_grant", "bad creds"
            )
            resp = await _handle_password_grant(svc, client, "u", "p", "")
            assert resp.status_code == 400
            assert b"invalid_grant" in resp.body

        asyncio.run(_run())


class TestAuthorizeRoute:
    """Unit tests for GET /oauth2/authorize."""

    @patch("shomer.routes.oauth2.AuthorizeService")
    def test_safe_redirect_on_unsupported_response_type(
        self, mock_cls: MagicMock
    ) -> None:
        """Error with safe code redirects to redirect_uri."""

        async def _run() -> None:
            mock_svc = AsyncMock()
            mock_svc.validate_request.side_effect = AuthorizeError(
                "unsupported_response_type", "bad response_type"
            )
            mock_cls.return_value = mock_svc
            req = MagicMock()
            db = AsyncMock()
            resp = await authorize(
                req,
                db,
                client_id="c",
                redirect_uri="https://app.example.com/cb",
                response_type="token",
                scope="openid",
                state="xyz",
            )
            assert resp.status_code == 302
            assert "unsupported_response_type" in resp.headers["location"]

        asyncio.run(_run())

    @patch("shomer.routes.oauth2._render_oauth2_error")
    @patch("shomer.routes.oauth2.AuthorizeService")
    def test_unsafe_error_renders_error_page(
        self, mock_cls: MagicMock, mock_render: MagicMock
    ) -> None:
        """Non-safe error (invalid_request) renders error page instead of redirect."""

        async def _run() -> None:
            mock_svc = AsyncMock()
            mock_svc.validate_request.side_effect = AuthorizeError(
                "invalid_request", "client_id is required"
            )
            mock_cls.return_value = mock_svc
            mock_render.return_value = MagicMock(status_code=400)
            req = MagicMock()
            db = AsyncMock()
            resp = await authorize(
                req,
                db,
                client_id=None,
                redirect_uri=None,
                response_type="code",
                scope="",
                state="xyz",
            )
            mock_render.assert_called_once()
            assert resp.status_code == 400

        asyncio.run(_run())

    @patch("shomer.routes.oauth2.SessionService")
    @patch("shomer.routes.oauth2.AuthorizeService")
    def test_unauthenticated_redirects_to_login(
        self, mock_auth_cls: MagicMock, mock_sess_cls: MagicMock
    ) -> None:
        """No session redirects to /ui/login."""

        async def _run() -> None:
            mock_auth_svc = AsyncMock()
            mock_auth_svc.validate_request.return_value = MagicMock()
            mock_auth_cls.return_value = mock_auth_svc

            mock_sess = AsyncMock()
            mock_sess.validate.return_value = None
            mock_sess_cls.return_value = mock_sess

            req = MagicMock()
            req.cookies.get.return_value = None
            req.url = "http://test/oauth2/authorize?client_id=c&state=x"
            db = AsyncMock()

            resp = await authorize(
                req,
                db,
                client_id="c",
                redirect_uri="https://a.com/cb",
                response_type="code",
                scope="openid",
                state="xyz",
            )
            assert resp.status_code == 302
            assert "/ui/login" in resp.headers["location"]

        asyncio.run(_run())

    @patch("shomer.routes.oauth2.SessionService")
    @patch("shomer.routes.oauth2.OAuth2ClientService")
    @patch("shomer.routes.oauth2.AuthorizeService")
    def test_consent_page_rendered(
        self,
        mock_auth_cls: MagicMock,
        mock_client_cls: MagicMock,
        mock_sess_cls: MagicMock,
    ) -> None:
        """Authenticated user sees the consent page."""

        async def _run() -> None:
            mock_request = MagicMock()
            mock_request.validated_scopes = ["openid"]
            mock_auth_svc = AsyncMock()
            mock_auth_request = MagicMock()
            mock_auth_request.validated_scopes = ["openid"]
            mock_auth_request.client_id = "c"
            mock_auth_request.redirect_uri = "https://a.com/cb"
            mock_auth_request.response_type = "code"
            mock_auth_request.scope = "openid"
            mock_auth_request.state = "xyz"
            mock_auth_request.nonce = None
            mock_auth_request.code_challenge = None
            mock_auth_request.code_challenge_method = None
            mock_auth_svc.validate_request.return_value = mock_auth_request
            mock_auth_cls.return_value = mock_auth_svc

            mock_client = MagicMock()
            mock_client.client_name = "Test"
            mock_client.logo_uri = None
            mock_client.policy_uri = None
            mock_client.tos_uri = None
            mock_client_svc = AsyncMock()
            mock_client_svc.get_by_client_id.return_value = mock_client
            mock_client_cls.return_value = mock_client_svc

            mock_session = MagicMock()
            mock_session.csrf_token = "csrf"
            mock_sess = AsyncMock()
            mock_sess.validate.return_value = mock_session
            mock_sess_cls.return_value = mock_sess

            req = MagicMock()
            req.cookies.get.return_value = "valid-token"
            db = AsyncMock()

            with patch("shomer.app.templates") as mock_tpl:
                mock_tpl.TemplateResponse.return_value = MagicMock()
                await authorize(
                    req,
                    db,
                    client_id="c",
                    redirect_uri="https://a.com/cb",
                    response_type="code",
                    scope="openid",
                    state="xyz",
                )
                mock_tpl.TemplateResponse.assert_called_once()
                call_args = mock_tpl.TemplateResponse.call_args
                ctx = call_args[0][2] if len(call_args[0]) > 2 else call_args[1]
                assert ctx["client_name"] == "Test"
                assert ctx["csrf_token"] == "csrf"

        asyncio.run(_run())


class TestAuthorizeConsent:
    """Unit tests for POST /oauth2/authorize (consent)."""

    @patch("shomer.routes.oauth2.SessionService")
    def test_no_session_raises_401(self, mock_cls: MagicMock) -> None:
        async def _run() -> None:
            req = MagicMock()
            req.cookies.get.return_value = None
            import pytest

            with pytest.raises(HTTPException) as exc_info:
                await authorize_consent(
                    req,
                    AsyncMock(),
                    "approve",
                    "csrf",
                    "c",
                    "https://a.com/cb",
                    "code",
                    "",
                    "xyz",
                    "",
                    "",
                    "",
                )
            assert exc_info.value.status_code == 401

        asyncio.run(_run())

    @patch("shomer.core.security.constant_time_compare", return_value=False)
    @patch("shomer.routes.oauth2.SessionService")
    def test_wrong_csrf_raises_403(
        self, mock_cls: MagicMock, mock_cmp: MagicMock
    ) -> None:
        async def _run() -> None:
            mock_session = MagicMock(csrf_token="real")
            mock_svc = AsyncMock()
            mock_svc.validate.return_value = mock_session
            mock_cls.return_value = mock_svc
            req = MagicMock()
            req.cookies.get.return_value = "tok"
            import pytest

            with pytest.raises(HTTPException) as exc_info:
                await authorize_consent(
                    req,
                    AsyncMock(),
                    "approve",
                    "wrong",
                    "c",
                    "https://a.com/cb",
                    "code",
                    "",
                    "xyz",
                    "",
                    "",
                    "",
                )
            assert exc_info.value.status_code == 403

        asyncio.run(_run())

    @patch("shomer.core.security.constant_time_compare", return_value=True)
    @patch("shomer.routes.oauth2.SessionService")
    def test_deny_redirects_with_error(
        self, mock_cls: MagicMock, mock_cmp: MagicMock
    ) -> None:
        async def _run() -> None:
            mock_session = MagicMock(csrf_token="ok")
            mock_svc = AsyncMock()
            mock_svc.validate.return_value = mock_session
            mock_cls.return_value = mock_svc
            req = MagicMock()
            req.cookies.get.return_value = "tok"
            resp = await authorize_consent(
                req,
                AsyncMock(),
                "deny",
                "ok",
                "c",
                "https://a.com/cb",
                "code",
                "",
                "xyz",
                "",
                "",
                "",
            )
            assert resp.status_code == 302
            assert "access_denied" in resp.headers["location"]

        asyncio.run(_run())


class TestRenderOAuth2Error:
    """Unit tests for _render_oauth2_error helper."""

    @patch("shomer.app.templates")
    def test_renders_error_page(self, mock_tpl: MagicMock) -> None:
        mock_tpl.TemplateResponse.return_value = MagicMock(body=b"<html>error</html>")
        resp = _render_oauth2_error(MagicMock(), "invalid_request", "bad")
        assert resp.status_code == 400

    def test_friendly_messages_exist(self) -> None:
        assert "invalid_client" in _FRIENDLY_ERROR_MESSAGES
        assert "invalid_request" in _FRIENDLY_ERROR_MESSAGES
        assert "server_error" in _FRIENDLY_ERROR_MESSAGES
        for msg in _FRIENDLY_ERROR_MESSAGES.values():
            assert len(msg) > 0


class TestHandleRefreshToken:
    """Unit tests for _handle_refresh_token."""

    def test_missing_refresh_token(self) -> None:
        async def _run() -> None:
            from shomer.routes.oauth2 import _handle_refresh_token

            client = _mock_client(grant_types=["refresh_token"])
            svc = AsyncMock()
            resp = await _handle_refresh_token(svc, client, "")
            assert resp.status_code == 400
            assert b"required" in resp.body

        asyncio.run(_run())

    def test_grant_not_allowed(self) -> None:
        async def _run() -> None:
            from shomer.routes.oauth2 import _handle_refresh_token

            client = _mock_client(grant_types=["authorization_code"])
            svc = AsyncMock()
            resp = await _handle_refresh_token(svc, client, "tok")
            assert resp.status_code == 400
            assert b"not authorized" in resp.body

        asyncio.run(_run())

    def test_success(self) -> None:
        async def _run() -> None:
            from shomer.routes.oauth2 import _handle_refresh_token

            client = _mock_client(grant_types=["refresh_token"])
            svc = AsyncMock()
            svc.rotate_refresh_token.return_value = TokenResponse(
                access_token="new-at", refresh_token="new-rt"
            )
            resp = await _handle_refresh_token(svc, client, "old-rt")
            assert resp.status_code == 200
            assert b"new-at" in resp.body

        asyncio.run(_run())

    def test_token_error(self) -> None:
        async def _run() -> None:
            from shomer.routes.oauth2 import _handle_refresh_token

            client = _mock_client(grant_types=["refresh_token"])
            svc = AsyncMock()
            svc.rotate_refresh_token.side_effect = TokenError(
                "invalid_grant", "expired"
            )
            resp = await _handle_refresh_token(svc, client, "tok")
            assert resp.status_code == 400
            assert b"invalid_grant" in resp.body

        asyncio.run(_run())


class TestRevokeEndpoint:
    """Unit tests for POST /oauth2/revoke."""

    def test_revoke_returns_200(self) -> None:
        async def _run() -> None:
            from shomer.routes.oauth2 import revoke

            with (
                patch("shomer.routes.oauth2.OAuth2ClientService") as mock_cls,
                patch(
                    "shomer.services.revocation_service.RevocationService"
                ) as mock_rev_cls,
            ):
                mock_client = MagicMock()
                mock_client.client_id = "c"
                mock_svc = AsyncMock()
                mock_svc.authenticate_client.return_value = mock_client
                mock_cls.return_value = mock_svc

                mock_rev = AsyncMock()
                mock_rev_cls.return_value = mock_rev

                req = MagicMock()
                req.headers.get.return_value = None
                db = AsyncMock()

                resp = await revoke(req, db, "tok", "refresh_token", "c", "s")
                assert resp.status_code == 200
                mock_rev.revoke.assert_awaited_once()

        asyncio.run(_run())

    def test_revoke_invalid_client_returns_401(self) -> None:
        async def _run() -> None:
            from shomer.routes.oauth2 import revoke

            with patch("shomer.routes.oauth2.OAuth2ClientService") as mock_cls:
                mock_svc = AsyncMock()
                mock_svc.authenticate_client.side_effect = InvalidClientError("bad")
                mock_cls.return_value = mock_svc

                req = MagicMock()
                req.headers.get.return_value = None
                db = AsyncMock()

                resp = await revoke(req, db, "tok", "", "", "")
                assert resp.status_code == 401

        asyncio.run(_run())


class TestIntrospectEndpoint:
    """Unit tests for POST /oauth2/introspect."""

    def test_introspect_returns_result(self) -> None:
        async def _run() -> None:
            from shomer.routes.oauth2 import introspect

            with (
                patch("shomer.routes.oauth2.OAuth2ClientService") as mock_cls,
                patch(
                    "shomer.services.introspection_service.IntrospectionService"
                ) as mock_intro_cls,
            ):
                mock_client = MagicMock()
                mock_svc = AsyncMock()
                mock_svc.authenticate_client.return_value = mock_client
                mock_cls.return_value = mock_svc

                mock_intro = AsyncMock()
                mock_intro.introspect.return_value = {"active": True, "scope": "openid"}
                mock_intro_cls.return_value = mock_intro

                req = MagicMock()
                req.headers.get.return_value = None
                db = AsyncMock()

                resp = await introspect(req, db, "tok", "access_token", "c", "s")
                assert resp.status_code == 200
                import json

                body = json.loads(bytes(resp.body))
                assert body["active"] is True

        asyncio.run(_run())

    def test_introspect_invalid_client(self) -> None:
        async def _run() -> None:
            from shomer.routes.oauth2 import introspect

            with patch("shomer.routes.oauth2.OAuth2ClientService") as mock_cls:
                mock_svc = AsyncMock()
                mock_svc.authenticate_client.side_effect = InvalidClientError("bad")
                mock_cls.return_value = mock_svc

                req = MagicMock()
                req.headers.get.return_value = None
                db = AsyncMock()

                resp = await introspect(req, db, "tok", "", "", "")
                assert resp.status_code == 401

        asyncio.run(_run())


class TestDeviceAuthEndpoint:
    """Unit tests for POST /oauth2/device."""

    def test_device_auth_success(self) -> None:
        async def _run() -> None:
            from shomer.routes.oauth2 import device_authorization
            from shomer.services.device_auth_service import DeviceAuthResponse

            with (
                patch("shomer.routes.oauth2.OAuth2ClientService") as mock_cls,
                patch(
                    "shomer.services.device_auth_service.DeviceAuthService"
                ) as mock_da_cls,
            ):
                mock_client = MagicMock()
                mock_client.client_id = "tv-app"
                mock_svc = AsyncMock()
                mock_svc.authenticate_client.return_value = mock_client
                mock_cls.return_value = mock_svc

                mock_da = AsyncMock()
                mock_da.create_device_code.return_value = DeviceAuthResponse(
                    device_code="dev-123",
                    user_code="ABCD-EFGH",
                    verification_uri="https://auth.local/ui/device",
                    verification_uri_complete="https://auth.local/ui/device?user_code=ABCD-EFGH",
                )
                mock_da_cls.return_value = mock_da

                req = MagicMock()
                req.headers.get.return_value = None
                db = AsyncMock()

                resp = await device_authorization(req, db, "openid", "tv-app", "secret")
                assert resp.status_code == 200
                import json

                body = json.loads(bytes(resp.body))
                assert body["device_code"] == "dev-123"
                assert body["user_code"] == "ABCD-EFGH"
                assert "verification_uri" in body
                assert "expires_in" in body
                assert "interval" in body

        asyncio.run(_run())

    def test_device_auth_invalid_client(self) -> None:
        async def _run() -> None:
            from shomer.routes.oauth2 import device_authorization

            with patch("shomer.routes.oauth2.OAuth2ClientService") as mock_cls:
                mock_svc = AsyncMock()
                mock_svc.authenticate_client.side_effect = InvalidClientError("bad")
                mock_cls.return_value = mock_svc

                req = MagicMock()
                req.headers.get.return_value = None
                db = AsyncMock()

                resp = await device_authorization(req, db, "", "", "")
                assert resp.status_code == 401

        asyncio.run(_run())

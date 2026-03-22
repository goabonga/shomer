# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Pure unit tests for federation callback route handler."""

from __future__ import annotations

import asyncio
import base64
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from shomer.routes.federation import federation_callback


class TestFederationCallbackIdPError:
    """Tests for IdP error handling."""

    def test_idp_error_redirects_to_login(self) -> None:
        async def _run() -> None:
            req = MagicMock()
            db = AsyncMock()
            resp = await federation_callback(
                req,
                db,
                code=None,
                state=None,
                error="access_denied",
                error_description="User denied access",
            )
            assert resp.status_code == 302
            assert "federation_failed" in resp.headers["location"]
            assert "denied" in resp.headers["location"]

        asyncio.run(_run())

    def test_idp_error_without_description(self) -> None:
        async def _run() -> None:
            req = MagicMock()
            db = AsyncMock()
            resp = await federation_callback(
                req,
                db,
                code=None,
                state=None,
                error="server_error",
                error_description=None,
            )
            assert resp.status_code == 302
            assert "server_error" in resp.headers["location"]

        asyncio.run(_run())


class TestFederationCallbackMissingParams:
    """Tests for missing required parameters."""

    def test_missing_code_redirects(self) -> None:
        async def _run() -> None:
            req = MagicMock()
            db = AsyncMock()
            resp = await federation_callback(
                req,
                db,
                code=None,
                state="some-state",
                error=None,
                error_description=None,
            )
            assert resp.status_code == 302
            assert "Missing" in resp.headers["location"]

        asyncio.run(_run())

    def test_missing_state_redirects(self) -> None:
        async def _run() -> None:
            req = MagicMock()
            db = AsyncMock()
            resp = await federation_callback(
                req,
                db,
                code="auth-code",
                state=None,
                error=None,
                error_description=None,
            )
            assert resp.status_code == 302
            assert "Missing" in resp.headers["location"]

        asyncio.run(_run())


class TestFederationCallbackStateDecoding:
    """Tests for state parameter decoding."""

    def test_invalid_state_redirects(self) -> None:
        async def _run() -> None:
            req = MagicMock()
            db = AsyncMock()
            resp = await federation_callback(
                req,
                db,
                code="code",
                state="not-valid-base64!!!",
                error=None,
                error_description=None,
            )
            assert resp.status_code == 302
            assert "Invalid" in resp.headers["location"]

        asyncio.run(_run())

    def test_state_missing_tenant_redirects(self) -> None:
        async def _run() -> None:
            state = base64.urlsafe_b64encode(
                json.dumps({"idp_id": "123"}).encode()
            ).decode()
            req = MagicMock()
            db = AsyncMock()
            resp = await federation_callback(
                req,
                db,
                code="code",
                state=state,
                error=None,
                error_description=None,
            )
            assert resp.status_code == 302
            assert "Invalid+state" in resp.headers["location"]

        asyncio.run(_run())

    def test_state_missing_idp_redirects(self) -> None:
        async def _run() -> None:
            state = base64.urlsafe_b64encode(
                json.dumps({"tenant_slug": "acme"}).encode()
            ).decode()
            req = MagicMock()
            db = AsyncMock()
            resp = await federation_callback(
                req,
                db,
                code="code",
                state=state,
                error=None,
                error_description=None,
            )
            assert resp.status_code == 302
            assert "Invalid+state" in resp.headers["location"]

        asyncio.run(_run())


class TestFederationCallbackIdPLookup:
    """Tests for IdP lookup."""

    def test_idp_not_found_redirects(self) -> None:
        async def _run() -> None:
            state = base64.urlsafe_b64encode(
                json.dumps({"tenant_slug": "acme", "idp_id": "unknown"}).encode()
            ).decode()

            with patch("shomer.routes.federation.FederationService") as mock_cls:
                mock_svc = AsyncMock()
                mock_svc.get_identity_provider.return_value = None
                mock_cls.return_value = mock_svc

                req = MagicMock()
                db = AsyncMock()
                resp = await federation_callback(
                    req,
                    db,
                    code="code",
                    state=state,
                    error=None,
                    error_description=None,
                )
                assert resp.status_code == 302
                assert "not+found" in resp.headers["location"]

        asyncio.run(_run())


class TestFederationCallbackSuccess:
    """Tests for successful callback flow."""

    def test_success_creates_session_and_redirects(self) -> None:
        async def _run() -> None:
            idp_id = str(uuid.uuid4())
            state_data = {
                "tenant_slug": "acme",
                "idp_id": idp_id,
                "code_verifier": "verifier",
                "redirect_uri": "/dashboard",
                "original_state": "orig-state",
            }
            state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

            mock_idp = MagicMock()
            mock_idp.name = "Google"
            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()
            mock_fed_id = MagicMock()
            mock_user_info = MagicMock()
            mock_user_info.subject = "google-123"
            mock_user_info.email = "user@acme.com"

            mock_session = MagicMock()
            mock_session.csrf_token = "csrf-tok"

            mock_policy = MagicMock()
            mock_policy.httponly = True
            mock_policy.secure = False
            mock_policy.samesite = "lax"
            mock_policy.domain = None

            with (
                patch("shomer.routes.federation.FederationService") as mock_fed_cls,
                patch("shomer.services.session_service.SessionService") as mock_sess_cls,
                patch(
                    "shomer.middleware.cookies.get_cookie_policy",
                    return_value=mock_policy,
                ),
            ):
                mock_svc = AsyncMock()
                mock_svc.get_identity_provider.return_value = mock_idp
                mock_svc.exchange_code_for_tokens.return_value = {
                    "access_token": "at",
                    "id_token": "idt",
                }
                mock_svc.get_user_info.return_value = mock_user_info
                mock_svc.find_or_create_user.return_value = (
                    mock_user,
                    mock_fed_id,
                    True,
                )
                mock_fed_cls.return_value = mock_svc

                mock_sess_svc = AsyncMock()
                mock_sess_svc.create.return_value = (mock_session, "raw-tok")
                mock_sess_cls.return_value = mock_sess_svc

                req = MagicMock()
                req.headers = MagicMock()
                req.headers.get = MagicMock(side_effect=lambda k, d="": d)
                req.url = MagicMock()
                req.url.scheme = "https"
                req.url.netloc = "acme.shomer.io"
                req.client.host = "127.0.0.1"
                db = AsyncMock()

                resp = await federation_callback(
                    req,
                    db,
                    code="auth-code",
                    state=state,
                    error=None,
                    error_description=None,
                )
                assert resp.status_code == 302
                assert "/dashboard" in resp.headers["location"]
                assert "state=orig-state" in resp.headers["location"]

        asyncio.run(_run())

    def test_success_without_redirect_uri_goes_to_profile(self) -> None:
        async def _run() -> None:
            state_data = {
                "tenant_slug": "acme",
                "idp_id": str(uuid.uuid4()),
            }
            state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

            mock_idp = MagicMock()
            mock_idp.name = "Google"
            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()
            mock_user_info = MagicMock()
            mock_user_info.subject = "sub"
            mock_user_info.email = "u@b.com"

            mock_session = MagicMock()
            mock_session.csrf_token = "csrf"

            mock_policy = MagicMock()
            mock_policy.httponly = True
            mock_policy.secure = False
            mock_policy.samesite = "lax"
            mock_policy.domain = None

            with (
                patch("shomer.routes.federation.FederationService") as mock_fed_cls,
                patch("shomer.services.session_service.SessionService") as mock_sess_cls,
                patch(
                    "shomer.middleware.cookies.get_cookie_policy",
                    return_value=mock_policy,
                ),
            ):
                mock_svc = AsyncMock()
                mock_svc.get_identity_provider.return_value = mock_idp
                mock_svc.exchange_code_for_tokens.return_value = {"access_token": "at"}
                mock_svc.get_user_info.return_value = mock_user_info
                mock_svc.find_or_create_user.return_value = (
                    mock_user,
                    MagicMock(),
                    False,
                )
                mock_fed_cls.return_value = mock_svc

                mock_sess_svc = AsyncMock()
                mock_sess_svc.create.return_value = (mock_session, "tok")
                mock_sess_cls.return_value = mock_sess_svc

                req = MagicMock()
                req.headers = MagicMock()
                req.headers.get = MagicMock(side_effect=lambda k, d="": d)
                req.url = MagicMock()
                req.url.scheme = "https"
                req.url.netloc = "shomer.io"
                req.client.host = "127.0.0.1"
                db = AsyncMock()

                resp = await federation_callback(
                    req,
                    db,
                    code="code",
                    state=state,
                    error=None,
                    error_description=None,
                )
                assert resp.status_code == 302
                assert "/ui/settings/profile" in resp.headers["location"]

        asyncio.run(_run())


class TestFederationCallbackErrorRecovery:
    """Tests for graceful error recovery."""

    def test_value_error_redirects_to_login(self) -> None:
        async def _run() -> None:
            state_data = {
                "tenant_slug": "acme",
                "idp_id": str(uuid.uuid4()),
            }
            state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

            mock_idp = MagicMock()
            mock_idp.name = "Test"

            with patch("shomer.routes.federation.FederationService") as mock_cls:
                mock_svc = AsyncMock()
                mock_svc.get_identity_provider.return_value = mock_idp
                mock_svc.exchange_code_for_tokens.return_value = {"access_token": "at"}
                mock_svc.get_user_info.side_effect = ValueError("Bad token")
                mock_cls.return_value = mock_svc

                req = MagicMock()
                req.headers = MagicMock()
                req.headers.get = MagicMock(side_effect=lambda k, d="": d)
                req.url = MagicMock()
                req.url.scheme = "https"
                req.url.netloc = "shomer.io"
                db = AsyncMock()

                resp = await federation_callback(
                    req,
                    db,
                    code="code",
                    state=state,
                    error=None,
                    error_description=None,
                )
                assert resp.status_code == 302
                assert (
                    "Bad+token" in resp.headers["location"]
                    or "Bad" in resp.headers["location"]
                )

        asyncio.run(_run())

    def test_generic_exception_redirects_to_login(self) -> None:
        async def _run() -> None:
            state_data = {
                "tenant_slug": "acme",
                "idp_id": str(uuid.uuid4()),
            }
            state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

            mock_idp = MagicMock()
            mock_idp.name = "Test"

            with patch("shomer.routes.federation.FederationService") as mock_cls:
                mock_svc = AsyncMock()
                mock_svc.get_identity_provider.return_value = mock_idp
                mock_svc.exchange_code_for_tokens.side_effect = RuntimeError(
                    "Connection failed"
                )
                mock_cls.return_value = mock_svc

                req = MagicMock()
                req.headers = MagicMock()
                req.headers.get = MagicMock(side_effect=lambda k, d="": d)
                req.url = MagicMock()
                req.url.scheme = "https"
                req.url.netloc = "shomer.io"
                db = AsyncMock()

                resp = await federation_callback(
                    req,
                    db,
                    code="code",
                    state=state,
                    error=None,
                    error_description=None,
                )
                assert resp.status_code == 302
                assert "unexpected" in resp.headers["location"].lower()

        asyncio.run(_run())

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for AuthorizeService."""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from shomer.services.authorize_service import AuthorizeError, AuthorizeService
from shomer.services.oauth2_client_service import InvalidRedirectURIError


def _make_mock_client(
    *,
    client_id: str = "test-client",
    redirect_uris: list[str] | None = None,
    response_types: list[str] | None = None,
    scopes: list[str] | None = None,
) -> MagicMock:
    """Create a mock OAuth2Client with the given attributes."""
    client = MagicMock()
    client.client_id = client_id
    client.redirect_uris = redirect_uris or ["https://app.example.com/callback"]
    client.response_types = response_types or ["code"]
    client.scopes = scopes or ["openid", "profile"]
    return client


class TestValidateRequest:
    """Tests for AuthorizeService.validate_request()."""

    def test_valid_request(self) -> None:
        """A fully valid request returns an AuthorizeRequest."""

        async def _run() -> None:
            db = AsyncMock()
            mock_client = _make_mock_client()

            with patch.object(AuthorizeService, "__init__", lambda self, session: None):
                svc = AuthorizeService.__new__(AuthorizeService)
                svc.session = db
                svc.client_service = MagicMock()
                svc.client_service.get_by_client_id = AsyncMock(
                    return_value=mock_client
                )
                svc.client_service.validate_redirect_uri = MagicMock()

                req = await svc.validate_request(
                    client_id="test-client",
                    redirect_uri="https://app.example.com/callback",
                    response_type="code",
                    scope="openid profile",
                    state="xyz",
                )
                assert req.client_id == "test-client"
                assert req.validated_scopes == ["openid", "profile"]

        asyncio.run(_run())

    def test_missing_client_id(self) -> None:
        """Missing client_id raises AuthorizeError."""

        async def _run() -> None:
            db = AsyncMock()
            svc = AuthorizeService.__new__(AuthorizeService)
            svc.session = db
            svc.client_service = MagicMock()

            with pytest.raises(AuthorizeError, match="client_id"):
                await svc.validate_request(
                    client_id=None,
                    redirect_uri="https://app.example.com/cb",
                    response_type="code",
                    scope="openid",
                    state="xyz",
                )

        asyncio.run(_run())

    def test_unknown_client(self) -> None:
        """Unknown client_id raises AuthorizeError."""

        async def _run() -> None:
            db = AsyncMock()
            svc = AuthorizeService.__new__(AuthorizeService)
            svc.session = db
            svc.client_service = MagicMock()
            svc.client_service.get_by_client_id = AsyncMock(return_value=None)

            with pytest.raises(AuthorizeError, match="Unknown"):
                await svc.validate_request(
                    client_id="nonexistent",
                    redirect_uri="https://app.example.com/cb",
                    response_type="code",
                    scope="openid",
                    state="xyz",
                )

        asyncio.run(_run())

    def test_invalid_redirect_uri(self) -> None:
        """Invalid redirect_uri raises AuthorizeError."""

        async def _run() -> None:
            db = AsyncMock()
            mock_client = _make_mock_client()

            svc = AuthorizeService.__new__(AuthorizeService)
            svc.session = db
            svc.client_service = MagicMock()
            svc.client_service.get_by_client_id = AsyncMock(return_value=mock_client)
            svc.client_service.validate_redirect_uri = MagicMock(
                side_effect=InvalidRedirectURIError("not registered")
            )

            with pytest.raises(AuthorizeError, match="not registered"):
                await svc.validate_request(
                    client_id="test-client",
                    redirect_uri="https://evil.com/cb",
                    response_type="code",
                    scope="openid",
                    state="xyz",
                )

        asyncio.run(_run())

    def test_missing_redirect_uri(self) -> None:
        """Missing redirect_uri raises AuthorizeError."""

        async def _run() -> None:
            db = AsyncMock()
            mock_client = _make_mock_client()

            svc = AuthorizeService.__new__(AuthorizeService)
            svc.session = db
            svc.client_service = MagicMock()
            svc.client_service.get_by_client_id = AsyncMock(return_value=mock_client)

            with pytest.raises(AuthorizeError, match="redirect_uri"):
                await svc.validate_request(
                    client_id="test-client",
                    redirect_uri=None,
                    response_type="code",
                    scope="openid",
                    state="xyz",
                )

        asyncio.run(_run())

    def test_unsupported_response_type(self) -> None:
        """Unsupported response_type raises AuthorizeError."""

        async def _run() -> None:
            db = AsyncMock()
            mock_client = _make_mock_client()

            svc = AuthorizeService.__new__(AuthorizeService)
            svc.session = db
            svc.client_service = MagicMock()
            svc.client_service.get_by_client_id = AsyncMock(return_value=mock_client)
            svc.client_service.validate_redirect_uri = MagicMock()

            with pytest.raises(AuthorizeError, match="Unsupported response_type"):
                await svc.validate_request(
                    client_id="test-client",
                    redirect_uri="https://app.example.com/callback",
                    response_type="token",
                    scope="openid",
                    state="xyz",
                )

        asyncio.run(_run())

    def test_missing_state(self) -> None:
        """Missing state raises AuthorizeError."""

        async def _run() -> None:
            db = AsyncMock()
            mock_client = _make_mock_client()

            svc = AuthorizeService.__new__(AuthorizeService)
            svc.session = db
            svc.client_service = MagicMock()
            svc.client_service.get_by_client_id = AsyncMock(return_value=mock_client)
            svc.client_service.validate_redirect_uri = MagicMock()

            with pytest.raises(AuthorizeError, match="state"):
                await svc.validate_request(
                    client_id="test-client",
                    redirect_uri="https://app.example.com/callback",
                    response_type="code",
                    scope="openid",
                    state=None,
                )

        asyncio.run(_run())

    def test_scope_validation_filters(self) -> None:
        """Scopes not in client's allowed list are filtered out."""

        async def _run() -> None:
            db = AsyncMock()
            mock_client = _make_mock_client(scopes=["openid", "profile"])

            svc = AuthorizeService.__new__(AuthorizeService)
            svc.session = db
            svc.client_service = MagicMock()
            svc.client_service.get_by_client_id = AsyncMock(return_value=mock_client)
            svc.client_service.validate_redirect_uri = MagicMock()

            req = await svc.validate_request(
                client_id="test-client",
                redirect_uri="https://app.example.com/callback",
                response_type="code",
                scope="openid profile email",
                state="xyz",
            )
            assert "email" not in req.validated_scopes
            assert "openid" in req.validated_scopes

        asyncio.run(_run())

    def test_pkce_parameters(self) -> None:
        """PKCE parameters are passed through to the request."""

        async def _run() -> None:
            db = AsyncMock()
            mock_client = _make_mock_client()

            svc = AuthorizeService.__new__(AuthorizeService)
            svc.session = db
            svc.client_service = MagicMock()
            svc.client_service.get_by_client_id = AsyncMock(return_value=mock_client)
            svc.client_service.validate_redirect_uri = MagicMock()

            req = await svc.validate_request(
                client_id="test-client",
                redirect_uri="https://app.example.com/callback",
                response_type="code",
                scope="openid",
                state="xyz",
                code_challenge="challenge123",
                code_challenge_method="S256",
            )
            assert req.code_challenge == "challenge123"
            assert req.code_challenge_method == "S256"

        asyncio.run(_run())

    def test_nonce_parameter(self) -> None:
        """Nonce is passed through to the request."""

        async def _run() -> None:
            db = AsyncMock()
            mock_client = _make_mock_client()

            svc = AuthorizeService.__new__(AuthorizeService)
            svc.session = db
            svc.client_service = MagicMock()
            svc.client_service.get_by_client_id = AsyncMock(return_value=mock_client)
            svc.client_service.validate_redirect_uri = MagicMock()

            req = await svc.validate_request(
                client_id="test-client",
                redirect_uri="https://app.example.com/callback",
                response_type="code",
                scope="openid",
                state="xyz",
                nonce="my-nonce",
            )
            assert req.nonce == "my-nonce"

        asyncio.run(_run())


class TestCreateAuthorizationCode:
    """Tests for AuthorizeService.create_authorization_code()."""

    def test_creates_code(self) -> None:
        """create_authorization_code returns a non-empty code string."""

        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            svc = AuthorizeService.__new__(AuthorizeService)
            svc.session = db
            svc.client_service = MagicMock()

            from shomer.services.authorize_service import AuthorizeRequest

            req = AuthorizeRequest(
                client_id="test-client",
                redirect_uri="https://app.example.com/callback",
                response_type="code",
                scope="openid",
                state="xyz",
                validated_scopes=["openid"],
            )
            user_id = uuid.uuid4()
            code = await svc.create_authorization_code(request=req, user_id=user_id)
            assert code is not None
            assert len(code) > 10
            db.add.assert_called_once()

        asyncio.run(_run())


class TestAuthorizeServiceInit:
    """Tests for AuthorizeService.__init__."""

    def test_constructor_sets_session_and_client_service(self) -> None:
        db = AsyncMock()
        svc = AuthorizeService(db)
        assert svc.session is db
        assert svc.client_service is not None


class TestValidateRequestEdgeCases:
    """Additional edge-case tests for validate_request coverage."""

    def test_missing_response_type(self) -> None:
        """response_type=None raises invalid_request."""

        async def _run() -> None:
            db = AsyncMock()
            mock_client = _make_mock_client()

            svc = AuthorizeService.__new__(AuthorizeService)
            svc.session = db
            svc.client_service = MagicMock()
            svc.client_service.get_by_client_id = AsyncMock(return_value=mock_client)
            svc.client_service.validate_redirect_uri = MagicMock()

            with pytest.raises(AuthorizeError, match="response_type is required"):
                await svc.validate_request(
                    client_id="test-client",
                    redirect_uri="https://app.example.com/callback",
                    response_type=None,
                    scope="openid",
                    state="xyz",
                )

        asyncio.run(_run())

    def test_client_not_authorized_for_code(self) -> None:
        """Client without 'code' in response_types raises unauthorized_client."""

        async def _run() -> None:
            db = AsyncMock()
            mock_client = _make_mock_client(response_types=["id_token"])

            svc = AuthorizeService.__new__(AuthorizeService)
            svc.session = db
            svc.client_service = MagicMock()
            svc.client_service.get_by_client_id = AsyncMock(return_value=mock_client)
            svc.client_service.validate_redirect_uri = MagicMock()

            with pytest.raises(AuthorizeError, match="not authorized"):
                await svc.validate_request(
                    client_id="test-client",
                    redirect_uri="https://app.example.com/callback",
                    response_type="code",
                    scope="openid",
                    state="xyz",
                )

        asyncio.run(_run())

    def test_unsupported_pkce_method(self) -> None:
        """Unsupported code_challenge_method raises invalid_request."""

        async def _run() -> None:
            db = AsyncMock()
            mock_client = _make_mock_client()

            svc = AuthorizeService.__new__(AuthorizeService)
            svc.session = db
            svc.client_service = MagicMock()
            svc.client_service.get_by_client_id = AsyncMock(return_value=mock_client)
            svc.client_service.validate_redirect_uri = MagicMock()

            with pytest.raises(AuthorizeError, match="Unsupported code_challenge"):
                await svc.validate_request(
                    client_id="test-client",
                    redirect_uri="https://app.example.com/callback",
                    response_type="code",
                    scope="openid",
                    state="xyz",
                    code_challenge="challenge",
                    code_challenge_method="RS256",
                )

        asyncio.run(_run())

    def test_public_client_requires_pkce(self) -> None:
        """Public client without code_challenge raises error."""
        from shomer.models.oauth2_client import ClientType

        async def _run() -> None:
            db = AsyncMock()
            mock_client = _make_mock_client()
            mock_client.client_type = ClientType.PUBLIC

            svc = AuthorizeService.__new__(AuthorizeService)
            svc.session = db
            svc.client_service = MagicMock()
            svc.client_service.get_by_client_id = AsyncMock(return_value=mock_client)
            svc.client_service.validate_redirect_uri = MagicMock()

            with pytest.raises(AuthorizeError, match="code_challenge is required"):
                await svc.validate_request(
                    client_id="test-client",
                    redirect_uri="https://app.example.com/callback",
                    response_type="code",
                    scope="openid",
                    state="xyz",
                )

        asyncio.run(_run())

    def test_public_client_with_pkce_succeeds(self) -> None:
        """Public client with code_challenge succeeds."""
        from shomer.models.oauth2_client import ClientType

        async def _run() -> None:
            db = AsyncMock()
            mock_client = _make_mock_client()
            mock_client.client_type = ClientType.PUBLIC

            svc = AuthorizeService.__new__(AuthorizeService)
            svc.session = db
            svc.client_service = MagicMock()
            svc.client_service.get_by_client_id = AsyncMock(return_value=mock_client)
            svc.client_service.validate_redirect_uri = MagicMock()

            req = await svc.validate_request(
                client_id="test-client",
                redirect_uri="https://app.example.com/callback",
                response_type="code",
                scope="openid",
                state="xyz",
                code_challenge="challenge123",
                code_challenge_method="S256",
            )
            assert req.code_challenge == "challenge123"
            assert req.code_challenge_method == "S256"

        asyncio.run(_run())

    def test_confidential_client_pkce_optional(self) -> None:
        """Confidential client without code_challenge succeeds."""
        from shomer.models.oauth2_client import ClientType

        async def _run() -> None:
            db = AsyncMock()
            mock_client = _make_mock_client()
            mock_client.client_type = ClientType.CONFIDENTIAL

            svc = AuthorizeService.__new__(AuthorizeService)
            svc.session = db
            svc.client_service = MagicMock()
            svc.client_service.get_by_client_id = AsyncMock(return_value=mock_client)
            svc.client_service.validate_redirect_uri = MagicMock()

            req = await svc.validate_request(
                client_id="test-client",
                redirect_uri="https://app.example.com/callback",
                response_type="code",
                scope="openid",
                state="xyz",
            )
            assert req.code_challenge is None

        asyncio.run(_run())

    def test_code_challenge_method_defaults_to_s256(self) -> None:
        """code_challenge without method defaults to S256."""

        async def _run() -> None:
            db = AsyncMock()
            mock_client = _make_mock_client()

            svc = AuthorizeService.__new__(AuthorizeService)
            svc.session = db
            svc.client_service = MagicMock()
            svc.client_service.get_by_client_id = AsyncMock(return_value=mock_client)
            svc.client_service.validate_redirect_uri = MagicMock()

            req = await svc.validate_request(
                client_id="test-client",
                redirect_uri="https://app.example.com/callback",
                response_type="code",
                scope="openid",
                state="xyz",
                code_challenge="challenge123",
                code_challenge_method=None,
            )
            assert req.code_challenge_method == "S256"

        asyncio.run(_run())

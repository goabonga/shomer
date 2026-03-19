# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for OAuth2ClientService."""

from __future__ import annotations

import asyncio
import base64
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from shomer.models.oauth2_client import (
    ClientType,
    TokenEndpointAuthMethod,
)
from shomer.services.oauth2_client_service import (
    InvalidClientError,
    InvalidRedirectURIError,
    OAuth2ClientService,
)


class TestCreateClient:
    """Tests for OAuth2ClientService.create_client()."""

    def test_creates_confidential_client(self) -> None:
        """Confidential client gets a client_id, secret, and correct defaults."""

        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            svc = OAuth2ClientService(db)
            client, secret = await svc.create_client(
                client_name="My App",
                redirect_uris=["https://app.example.com/callback"],
            )
            assert client.client_id is not None
            assert secret is not None
            assert client.client_secret_hash is not None
            assert client.client_type == ClientType.CONFIDENTIAL
            assert (
                client.token_endpoint_auth_method
                == TokenEndpointAuthMethod.CLIENT_SECRET_BASIC
            )

        asyncio.run(_run())

    def test_creates_public_client(self) -> None:
        """Public client has no secret and auth_method=NONE."""

        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            svc = OAuth2ClientService(db)
            client, secret = await svc.create_client(
                client_name="SPA",
                client_type=ClientType.PUBLIC,
                redirect_uris=["https://spa.example.com/callback"],
            )
            assert secret is None
            assert client.client_secret_hash is None
            assert client.client_type == ClientType.PUBLIC
            assert client.token_endpoint_auth_method == TokenEndpointAuthMethod.NONE

        asyncio.run(_run())

    def test_rejects_redirect_uri_with_fragment(self) -> None:
        """Redirect URI with fragment raises InvalidRedirectURIError."""

        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            svc = OAuth2ClientService(db)
            with pytest.raises(InvalidRedirectURIError, match="fragment"):
                await svc.create_client(
                    client_name="Bad",
                    redirect_uris=["https://app.example.com/cb#frag"],
                )

        asyncio.run(_run())

    def test_rejects_malformed_redirect_uri(self) -> None:
        """Malformed redirect URI raises InvalidRedirectURIError."""

        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            svc = OAuth2ClientService(db)
            with pytest.raises(InvalidRedirectURIError, match="Malformed"):
                await svc.create_client(
                    client_name="Bad",
                    redirect_uris=["not-a-uri"],
                )

        asyncio.run(_run())


class TestGetByClientId:
    """Tests for OAuth2ClientService.get_by_client_id()."""

    def test_finds_client(self) -> None:
        """Returns client when found by client_id."""

        async def _run() -> None:
            db = AsyncMock()
            mock_client = MagicMock()
            mock_client.client_id = "found-client"

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_client
            db.execute.return_value = result

            svc = OAuth2ClientService(db)
            found = await svc.get_by_client_id("found-client")
            assert found is not None
            assert found.client_id == "found-client"

        asyncio.run(_run())

    def test_returns_none_for_unknown(self) -> None:
        """Returns None for unknown client_id."""

        async def _run() -> None:
            db = AsyncMock()
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db.execute.return_value = result

            svc = OAuth2ClientService(db)
            assert await svc.get_by_client_id("nonexistent") is None

        asyncio.run(_run())


class TestAuthenticateClient:
    """Tests for OAuth2ClientService.authenticate_client()."""

    def test_basic_auth_success(self) -> None:
        """HTTP Basic auth with correct secret succeeds."""

        async def _run() -> None:
            db = AsyncMock()
            mock_client = MagicMock()
            mock_client.client_id = "app-client"
            mock_client.client_type = ClientType.CONFIDENTIAL
            mock_client.token_endpoint_auth_method = (
                TokenEndpointAuthMethod.CLIENT_SECRET_BASIC
            )
            mock_client.client_secret_hash = "$argon2id$hash"

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_client
            db.execute.return_value = result

            header = "Basic " + base64.b64encode(b"app-client:correct-secret").decode()

            with patch(
                "shomer.services.oauth2_client_service.verify_password",
                return_value=True,
            ):
                svc = OAuth2ClientService(db)
                authed = await svc.authenticate_client(authorization_header=header)
                assert authed.client_id == "app-client"

        asyncio.run(_run())

    def test_post_body_auth_success(self) -> None:
        """POST body auth with correct secret succeeds."""

        async def _run() -> None:
            db = AsyncMock()
            mock_client = MagicMock()
            mock_client.client_id = "post-client"
            mock_client.client_type = ClientType.CONFIDENTIAL
            mock_client.token_endpoint_auth_method = (
                TokenEndpointAuthMethod.CLIENT_SECRET_POST
            )
            mock_client.client_secret_hash = "$argon2id$hash"

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_client
            db.execute.return_value = result

            with patch(
                "shomer.services.oauth2_client_service.verify_password",
                return_value=True,
            ):
                svc = OAuth2ClientService(db)
                authed = await svc.authenticate_client(
                    body_client_id="post-client",
                    body_client_secret="correct-secret",
                )
                assert authed.client_id == "post-client"

        asyncio.run(_run())

    def test_none_auth_public_client(self) -> None:
        """Public client with auth_method=NONE succeeds without secret."""

        async def _run() -> None:
            db = AsyncMock()
            mock_client = MagicMock()
            mock_client.client_id = "pub-client"
            mock_client.client_type = ClientType.PUBLIC
            mock_client.token_endpoint_auth_method = TokenEndpointAuthMethod.NONE

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_client
            db.execute.return_value = result

            svc = OAuth2ClientService(db)
            authed = await svc.authenticate_client(
                body_client_id="pub-client",
            )
            assert authed.client_id == "pub-client"

        asyncio.run(_run())

    def test_wrong_secret_raises(self) -> None:
        """Wrong client secret raises InvalidClientError."""

        async def _run() -> None:
            db = AsyncMock()
            mock_client = MagicMock()
            mock_client.client_id = "app-client"
            mock_client.client_type = ClientType.CONFIDENTIAL
            mock_client.token_endpoint_auth_method = (
                TokenEndpointAuthMethod.CLIENT_SECRET_BASIC
            )
            mock_client.client_secret_hash = "$argon2id$hash"

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_client
            db.execute.return_value = result

            header = "Basic " + base64.b64encode(b"app-client:wrong").decode()

            with patch(
                "shomer.services.oauth2_client_service.verify_password",
                return_value=False,
            ):
                svc = OAuth2ClientService(db)
                with pytest.raises(InvalidClientError):
                    await svc.authenticate_client(authorization_header=header)

        asyncio.run(_run())

    def test_unknown_client_raises(self) -> None:
        """Unknown client raises InvalidClientError."""

        async def _run() -> None:
            db = AsyncMock()
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db.execute.return_value = result

            header = "Basic " + base64.b64encode(b"unknown:secret").decode()

            with patch("shomer.services.oauth2_client_service.hash_password"):
                svc = OAuth2ClientService(db)
                with pytest.raises(InvalidClientError):
                    await svc.authenticate_client(authorization_header=header)

        asyncio.run(_run())

    def test_missing_credentials_raises(self) -> None:
        """Missing all credentials raises InvalidClientError."""

        async def _run() -> None:
            db = AsyncMock()
            svc = OAuth2ClientService(db)
            with pytest.raises(InvalidClientError, match="Missing"):
                await svc.authenticate_client()

        asyncio.run(_run())

    def test_malformed_basic_header_raises(self) -> None:
        """Malformed Basic header raises InvalidClientError."""

        async def _run() -> None:
            db = AsyncMock()
            svc = OAuth2ClientService(db)
            with pytest.raises(InvalidClientError, match="Malformed"):
                await svc.authenticate_client(
                    authorization_header="Basic !!!invalid!!!"
                )

        asyncio.run(_run())


class TestRotateSecret:
    """Tests for OAuth2ClientService.rotate_secret()."""

    def test_rotates_secret(self) -> None:
        """Rotating produces a new secret and updates the hash."""

        async def _run() -> None:
            db = AsyncMock()
            mock_client = MagicMock()
            mock_client.client_id = "rotate-client"
            mock_client.client_type = ClientType.CONFIDENTIAL
            mock_client.client_secret_hash = "$argon2id$old"

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_client
            db.execute.return_value = result
            db.flush = AsyncMock()

            with patch("shomer.services.oauth2_client_service.hash_password") as mhash:
                mhash.return_value = "$argon2id$new"
                svc = OAuth2ClientService(db)
                rotated, new_secret = await svc.rotate_secret("rotate-client")
                assert new_secret is not None
                assert len(new_secret) > 10
                assert rotated.client_secret_hash == "$argon2id$new"

        asyncio.run(_run())

    def test_new_secret_works(self) -> None:
        """New secret after rotation can be verified."""

        async def _run() -> None:
            db = AsyncMock()
            mock_client = MagicMock()
            mock_client.client_id = "rotate-client"
            mock_client.client_type = ClientType.CONFIDENTIAL
            mock_client.client_secret_hash = "$argon2id$old"
            mock_client.token_endpoint_auth_method = (
                TokenEndpointAuthMethod.CLIENT_SECRET_BASIC
            )

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_client
            db.execute.return_value = result
            db.flush = AsyncMock()

            with patch("shomer.services.oauth2_client_service.hash_password") as mhash:
                mhash.return_value = "$argon2id$new"
                svc = OAuth2ClientService(db)
                _, new_secret = await svc.rotate_secret("rotate-client")

            # Verify the new hash was set
            assert mock_client.client_secret_hash == "$argon2id$new"

        asyncio.run(_run())

    def test_public_client_raises(self) -> None:
        """Rotating a public client's secret raises InvalidClientError."""

        async def _run() -> None:
            db = AsyncMock()
            mock_client = MagicMock()
            mock_client.client_id = "pub-client"
            mock_client.client_type = ClientType.PUBLIC

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_client
            db.execute.return_value = result

            svc = OAuth2ClientService(db)
            with pytest.raises(InvalidClientError, match="public"):
                await svc.rotate_secret("pub-client")

        asyncio.run(_run())


class TestValidateRedirectUri:
    """Tests for OAuth2ClientService.validate_redirect_uri()."""

    def test_valid_uri(self) -> None:
        """Registered URI passes validation."""

        async def _run() -> None:
            db = AsyncMock()
            mock_client = MagicMock()
            mock_client.redirect_uris = ["https://app.example.com/callback"]

            svc = OAuth2ClientService(db)
            # Should not raise
            svc.validate_redirect_uri(mock_client, "https://app.example.com/callback")

        asyncio.run(_run())

    def test_unregistered_uri_raises(self) -> None:
        """Unregistered URI raises InvalidRedirectURIError."""

        async def _run() -> None:
            db = AsyncMock()
            mock_client = MagicMock()
            mock_client.redirect_uris = ["https://app.example.com/callback"]

            svc = OAuth2ClientService(db)
            with pytest.raises(InvalidRedirectURIError, match="not registered"):
                svc.validate_redirect_uri(mock_client, "https://evil.com/callback")

        asyncio.run(_run())

    def test_fragment_uri_raises(self) -> None:
        """URI with fragment raises InvalidRedirectURIError."""

        async def _run() -> None:
            db = AsyncMock()
            mock_client = MagicMock()
            mock_client.redirect_uris = ["https://app.example.com/callback"]

            svc = OAuth2ClientService(db)
            with pytest.raises(InvalidRedirectURIError, match="fragment"):
                svc.validate_redirect_uri(
                    mock_client, "https://app.example.com/callback#bad"
                )

        asyncio.run(_run())

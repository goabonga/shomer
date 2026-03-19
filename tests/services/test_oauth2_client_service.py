# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for OAuth2ClientService."""

from __future__ import annotations

import asyncio
import base64
from collections.abc import Iterator

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from shomer.core.database import Base
from shomer.models.access_token import AccessToken  # noqa: F401
from shomer.models.jwk import JWK  # noqa: F401
from shomer.models.oauth2_client import (
    ClientType,
    TokenEndpointAuthMethod,
)
from shomer.models.password_reset_token import PasswordResetToken  # noqa: F401
from shomer.models.refresh_token import RefreshToken  # noqa: F401
from shomer.models.session import Session  # noqa: F401
from shomer.models.user import User  # noqa: F401
from shomer.models.user_email import UserEmail  # noqa: F401
from shomer.models.user_password import UserPassword  # noqa: F401
from shomer.models.user_profile import UserProfile  # noqa: F401
from shomer.models.verification_code import VerificationCode  # noqa: F401
from shomer.services.oauth2_client_service import (
    InvalidClientError,
    InvalidRedirectURIError,
    OAuth2ClientService,
)

_ENGINE = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_SESSION_FACTORY = async_sessionmaker(_ENGINE, expire_on_commit=False)


@pytest.fixture(autouse=True)
def _setup_db() -> Iterator[None]:
    async def _create() -> None:
        async with _ENGINE.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_create())
    yield

    async def _drop() -> None:
        async with _ENGINE.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    asyncio.run(_drop())


class TestCreateClient:
    """Tests for OAuth2ClientService.create_client()."""

    def test_creates_confidential_client(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
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
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
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
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = OAuth2ClientService(db)
                with pytest.raises(InvalidRedirectURIError, match="fragment"):
                    await svc.create_client(
                        client_name="Bad",
                        redirect_uris=["https://app.example.com/cb#frag"],
                    )

        asyncio.run(_run())

    def test_rejects_malformed_redirect_uri(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
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
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = OAuth2ClientService(db)
                client, _ = await svc.create_client(client_name="App")
                found = await svc.get_by_client_id(client.client_id)
                assert found is not None
                assert found.client_id == client.client_id

        asyncio.run(_run())

    def test_returns_none_for_unknown(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = OAuth2ClientService(db)
                assert await svc.get_by_client_id("nonexistent") is None

        asyncio.run(_run())


class TestAuthenticateClient:
    """Tests for OAuth2ClientService.authenticate_client()."""

    def test_basic_auth_success(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = OAuth2ClientService(db)
                client, secret = await svc.create_client(client_name="App")
                assert secret is not None
                header = (
                    "Basic "
                    + base64.b64encode(f"{client.client_id}:{secret}".encode()).decode()
                )
                authed = await svc.authenticate_client(authorization_header=header)
                assert authed.client_id == client.client_id

        asyncio.run(_run())

    def test_post_body_auth_success(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = OAuth2ClientService(db)
                client, secret = await svc.create_client(
                    client_name="App",
                    token_endpoint_auth_method=TokenEndpointAuthMethod.CLIENT_SECRET_POST,
                )
                assert secret is not None
                authed = await svc.authenticate_client(
                    body_client_id=client.client_id,
                    body_client_secret=secret,
                )
                assert authed.client_id == client.client_id

        asyncio.run(_run())

    def test_none_auth_public_client(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = OAuth2ClientService(db)
                client, _ = await svc.create_client(
                    client_name="SPA",
                    client_type=ClientType.PUBLIC,
                )
                authed = await svc.authenticate_client(
                    body_client_id=client.client_id,
                )
                assert authed.client_id == client.client_id

        asyncio.run(_run())

    def test_wrong_secret_raises(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = OAuth2ClientService(db)
                client, _ = await svc.create_client(client_name="App")
                header = (
                    "Basic "
                    + base64.b64encode(f"{client.client_id}:wrong".encode()).decode()
                )
                with pytest.raises(InvalidClientError):
                    await svc.authenticate_client(authorization_header=header)

        asyncio.run(_run())

    def test_unknown_client_raises(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = OAuth2ClientService(db)
                header = "Basic " + base64.b64encode(b"unknown:secret").decode()
                with pytest.raises(InvalidClientError):
                    await svc.authenticate_client(authorization_header=header)

        asyncio.run(_run())

    def test_missing_credentials_raises(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = OAuth2ClientService(db)
                with pytest.raises(InvalidClientError, match="Missing"):
                    await svc.authenticate_client()

        asyncio.run(_run())

    def test_malformed_basic_header_raises(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = OAuth2ClientService(db)
                with pytest.raises(InvalidClientError, match="Malformed"):
                    await svc.authenticate_client(
                        authorization_header="Basic !!!invalid!!!"
                    )

        asyncio.run(_run())


class TestRotateSecret:
    """Tests for OAuth2ClientService.rotate_secret()."""

    def test_rotates_secret(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = OAuth2ClientService(db)
                client, old_secret = await svc.create_client(client_name="App")
                assert old_secret is not None
                _, new_secret = await svc.rotate_secret(client.client_id)
                assert new_secret != old_secret
                # Old secret should no longer work
                header = (
                    "Basic "
                    + base64.b64encode(
                        f"{client.client_id}:{old_secret}".encode()
                    ).decode()
                )
                with pytest.raises(InvalidClientError):
                    await svc.authenticate_client(authorization_header=header)

        asyncio.run(_run())

    def test_new_secret_works(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = OAuth2ClientService(db)
                client, _ = await svc.create_client(client_name="App")
                _, new_secret = await svc.rotate_secret(client.client_id)
                header = (
                    "Basic "
                    + base64.b64encode(
                        f"{client.client_id}:{new_secret}".encode()
                    ).decode()
                )
                authed = await svc.authenticate_client(authorization_header=header)
                assert authed.client_id == client.client_id

        asyncio.run(_run())

    def test_public_client_raises(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = OAuth2ClientService(db)
                client, _ = await svc.create_client(
                    client_name="SPA", client_type=ClientType.PUBLIC
                )
                with pytest.raises(InvalidClientError, match="public"):
                    await svc.rotate_secret(client.client_id)

        asyncio.run(_run())


class TestValidateRedirectUri:
    """Tests for OAuth2ClientService.validate_redirect_uri()."""

    def test_valid_uri(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = OAuth2ClientService(db)
                client, _ = await svc.create_client(
                    client_name="App",
                    redirect_uris=["https://app.example.com/callback"],
                )
                svc.validate_redirect_uri(client, "https://app.example.com/callback")

        asyncio.run(_run())

    def test_unregistered_uri_raises(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = OAuth2ClientService(db)
                client, _ = await svc.create_client(
                    client_name="App",
                    redirect_uris=["https://app.example.com/callback"],
                )
                with pytest.raises(InvalidRedirectURIError, match="not registered"):
                    svc.validate_redirect_uri(client, "https://evil.com/callback")

        asyncio.run(_run())

    def test_fragment_uri_raises(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = OAuth2ClientService(db)
                client, _ = await svc.create_client(
                    client_name="App",
                    redirect_uris=["https://app.example.com/callback"],
                )
                with pytest.raises(InvalidRedirectURIError, match="fragment"):
                    svc.validate_redirect_uri(
                        client, "https://app.example.com/callback#bad"
                    )

        asyncio.run(_run())

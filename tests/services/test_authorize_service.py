# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for AuthorizeService."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from shomer.core.database import Base
from shomer.models.access_token import AccessToken  # noqa: F401
from shomer.models.authorization_code import AuthorizationCode  # noqa: F401
from shomer.models.jwk import JWK  # noqa: F401
from shomer.models.oauth2_client import ClientType, OAuth2Client  # noqa: F401
from shomer.models.password_reset_token import PasswordResetToken  # noqa: F401
from shomer.models.refresh_token import RefreshToken  # noqa: F401
from shomer.models.session import Session  # noqa: F401
from shomer.models.user import User  # noqa: F401
from shomer.models.user_email import UserEmail  # noqa: F401
from shomer.models.user_password import UserPassword  # noqa: F401
from shomer.models.user_profile import UserProfile  # noqa: F401
from shomer.models.verification_code import VerificationCode  # noqa: F401
from shomer.services.authorize_service import AuthorizeError, AuthorizeService
from shomer.services.oauth2_client_service import OAuth2ClientService

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


async def _create_client(
    db: object,
    redirect_uris: list[str] | None = None,
    response_types: list[str] | None = None,
    scopes: list[str] | None = None,
) -> str:
    """Create a test OAuth2 client and return its client_id."""
    svc = OAuth2ClientService(db)  # type: ignore[arg-type]
    client, _ = await svc.create_client(
        client_name="Test App",
        redirect_uris=redirect_uris or ["https://app.example.com/callback"],
        response_types=response_types or ["code"],
        grant_types=["authorization_code"],
        scopes=scopes or ["openid", "profile"],
    )
    return client.client_id


class TestValidateRequest:
    """Tests for AuthorizeService.validate_request()."""

    def test_valid_request(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                cid = await _create_client(db)
                svc = AuthorizeService(db)
                req = await svc.validate_request(
                    client_id=cid,
                    redirect_uri="https://app.example.com/callback",
                    response_type="code",
                    scope="openid profile",
                    state="xyz",
                )
                assert req.client_id == cid
                assert req.validated_scopes == ["openid", "profile"]

        asyncio.run(_run())

    def test_missing_client_id(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = AuthorizeService(db)
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
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = AuthorizeService(db)
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
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                cid = await _create_client(db)
                svc = AuthorizeService(db)
                with pytest.raises(AuthorizeError, match="not registered"):
                    await svc.validate_request(
                        client_id=cid,
                        redirect_uri="https://evil.com/cb",
                        response_type="code",
                        scope="openid",
                        state="xyz",
                    )

        asyncio.run(_run())

    def test_missing_redirect_uri(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                cid = await _create_client(db)
                svc = AuthorizeService(db)
                with pytest.raises(AuthorizeError, match="redirect_uri"):
                    await svc.validate_request(
                        client_id=cid,
                        redirect_uri=None,
                        response_type="code",
                        scope="openid",
                        state="xyz",
                    )

        asyncio.run(_run())

    def test_unsupported_response_type(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                cid = await _create_client(db)
                svc = AuthorizeService(db)
                with pytest.raises(AuthorizeError, match="Unsupported response_type"):
                    await svc.validate_request(
                        client_id=cid,
                        redirect_uri="https://app.example.com/callback",
                        response_type="token",
                        scope="openid",
                        state="xyz",
                    )

        asyncio.run(_run())

    def test_missing_state(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                cid = await _create_client(db)
                svc = AuthorizeService(db)
                with pytest.raises(AuthorizeError, match="state"):
                    await svc.validate_request(
                        client_id=cid,
                        redirect_uri="https://app.example.com/callback",
                        response_type="code",
                        scope="openid",
                        state=None,
                    )

        asyncio.run(_run())

    def test_scope_validation_filters(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                cid = await _create_client(db, scopes=["openid", "profile"])
                svc = AuthorizeService(db)
                req = await svc.validate_request(
                    client_id=cid,
                    redirect_uri="https://app.example.com/callback",
                    response_type="code",
                    scope="openid profile email",
                    state="xyz",
                )
                assert "email" not in req.validated_scopes
                assert "openid" in req.validated_scopes

        asyncio.run(_run())

    def test_pkce_parameters(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                cid = await _create_client(db)
                svc = AuthorizeService(db)
                req = await svc.validate_request(
                    client_id=cid,
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
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                cid = await _create_client(db)
                svc = AuthorizeService(db)
                req = await svc.validate_request(
                    client_id=cid,
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
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                cid = await _create_client(db)
                svc = AuthorizeService(db)
                req = await svc.validate_request(
                    client_id=cid,
                    redirect_uri="https://app.example.com/callback",
                    response_type="code",
                    scope="openid",
                    state="xyz",
                )
                user = User(username="test")
                db.add(user)
                await db.flush()
                code = await svc.create_authorization_code(request=req, user_id=user.id)
                assert code is not None
                assert len(code) > 10

        asyncio.run(_run())

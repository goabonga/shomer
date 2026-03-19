# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests to close remaining coverage gaps in services."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Iterator
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from shomer.core.database import Base
from shomer.core.security import hash_password
from shomer.models.access_token import AccessToken  # noqa: F401
from shomer.models.authorization_code import AuthorizationCode  # noqa: F401
from shomer.models.jwk import JWK  # noqa: F401
from shomer.models.oauth2_client import (
    ClientType,
    OAuth2Client,
    TokenEndpointAuthMethod,
)
from shomer.models.password_reset_token import PasswordResetToken  # noqa: F401
from shomer.models.queries import get_user_by_id
from shomer.models.refresh_token import RefreshToken  # noqa: F401
from shomer.models.session import Session
from shomer.models.user import User
from shomer.models.user_email import UserEmail
from shomer.models.user_password import UserPassword
from shomer.models.user_profile import UserProfile  # noqa: F401
from shomer.models.verification_code import VerificationCode  # noqa: F401
from shomer.services.oauth2_client_service import (
    InvalidClientError,
    OAuth2ClientService,
)
from shomer.services.session_service import SessionService

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


# --- models/queries.py: get_user_by_id ---


class TestGetUserById:
    """Tests for get_user_by_id query helper."""

    def test_returns_user_when_found(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                user = User(username="found")
                db.add(user)
                await db.flush()
                ue = UserEmail(
                    user_id=user.id,
                    email="f@example.com",
                    is_primary=True,
                )
                db.add(ue)
                pw = UserPassword(
                    user_id=user.id,
                    password_hash=hash_password("pw123456789"),
                )
                db.add(pw)
                await db.flush()

                result = await get_user_by_id(db, user.id)
                assert result is not None
                assert result.username == "found"

        asyncio.run(_run())

    def test_returns_none_when_not_found(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                result = await get_user_by_id(db, uuid.uuid4())
                assert result is None

        asyncio.run(_run())


# --- services/session_service.py: validate naive datetime ---


class TestSessionValidateNaiveDatetime:
    """Test session validation with naive (no-tzinfo) datetime from SQLite."""

    def test_valid_session_with_naive_datetime(self) -> None:
        """SQLite returns naive datetimes — validate must handle them."""
        import hashlib
        import warnings

        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                user = User(username="tz")
                db.add(user)
                await db.flush()
                raw = uuid.uuid4().hex
                thash = hashlib.sha256(raw.encode()).hexdigest()
                # Use naive datetime (no timezone) — mimics SQLite behavior
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", DeprecationWarning)
                    naive_now = datetime.utcnow()  # noqa: DTZ003
                    naive_future = naive_now + timedelta(hours=24)
                session = Session(
                    user_id=user.id,
                    token_hash=thash,
                    csrf_token=uuid.uuid4().hex,
                    last_activity=naive_now,
                    expires_at=naive_future,
                )
                db.add(session)
                await db.flush()

                svc = SessionService(db)
                result = await svc.validate(raw)
                assert result is not None

        asyncio.run(_run())


# --- services/oauth2_client_service.py: authenticate + rotate ---


class TestOAuth2ClientAuthenticateEdgeCases:
    """Tests for authenticate_client edge cases."""

    def test_none_method_public_client(self) -> None:
        """Public client with auth_method=NONE succeeds without secret."""

        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                client = OAuth2Client(
                    client_id="pub-client",
                    client_name="Public",
                    client_type=ClientType.PUBLIC,
                    redirect_uris=["https://app.example.com/cb"],
                    grant_types=["authorization_code"],
                    response_types=["code"],
                    scopes=["openid"],
                    contacts=[],
                    token_endpoint_auth_method=TokenEndpointAuthMethod.NONE,
                )
                db.add(client)
                await db.flush()

                svc = OAuth2ClientService(db)
                result = await svc.authenticate_client(
                    body_client_id="pub-client",
                )
                assert result.client_id == "pub-client"

        asyncio.run(_run())

    def test_none_method_confidential_client_raises(self) -> None:
        """Confidential client with auth_method=NONE raises error."""

        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                client = OAuth2Client(
                    client_id="conf-none",
                    client_name="Conf None",
                    client_type=ClientType.CONFIDENTIAL,
                    redirect_uris=[],
                    grant_types=[],
                    response_types=[],
                    scopes=[],
                    contacts=[],
                    token_endpoint_auth_method=TokenEndpointAuthMethod.NONE,
                )
                db.add(client)
                await db.flush()

                svc = OAuth2ClientService(db)
                with pytest.raises(InvalidClientError, match="only allowed for public"):
                    await svc.authenticate_client(body_client_id="conf-none")

        asyncio.run(_run())

    def test_secret_method_missing_secret_raises(self) -> None:
        """Secret-based auth without providing a secret raises error."""

        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = OAuth2ClientService(db)
                client, _ = await svc.create_client(
                    client_name="SecretRequired",
                    redirect_uris=["https://app.example.com/cb"],
                    response_types=["code"],
                    grant_types=["authorization_code"],
                    scopes=["openid"],
                )
                await db.flush()

                with pytest.raises(InvalidClientError, match="secret required"):
                    await svc.authenticate_client(
                        body_client_id=client.client_id,
                        body_client_secret=None,
                    )

        asyncio.run(_run())

    def test_secret_method_wrong_secret_raises(self) -> None:
        """Wrong client_secret raises error."""

        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = OAuth2ClientService(db)
                client, _ = await svc.create_client(
                    client_name="WrongSecret",
                    redirect_uris=["https://app.example.com/cb"],
                    response_types=["code"],
                    grant_types=["authorization_code"],
                    scopes=["openid"],
                )
                await db.flush()

                with pytest.raises(InvalidClientError, match="Invalid client"):
                    await svc.authenticate_client(
                        body_client_id=client.client_id,
                        body_client_secret="wrong-secret",
                    )

        asyncio.run(_run())


class TestRotateSecret:
    """Tests for OAuth2ClientService.rotate_secret."""

    def test_rotate_secret_success(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = OAuth2ClientService(db)
                client, _ = await svc.create_client(
                    client_name="Rotate",
                    redirect_uris=["https://a.com/cb"],
                    response_types=["code"],
                    grant_types=["authorization_code"],
                    scopes=["openid"],
                )
                await db.flush()
                rotated, new_secret = await svc.rotate_secret(client.client_id)
                assert new_secret is not None
                assert len(new_secret) > 10
                assert rotated.client_secret_hash is not None

        asyncio.run(_run())

    def test_rotate_secret_not_found_raises(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = OAuth2ClientService(db)
                with pytest.raises(InvalidClientError, match="not found"):
                    await svc.rotate_secret("nonexistent")

        asyncio.run(_run())

    def test_rotate_secret_public_client_raises(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                client = OAuth2Client(
                    client_id="pub-rotate",
                    client_name="PubRotate",
                    client_type=ClientType.PUBLIC,
                    redirect_uris=[],
                    grant_types=[],
                    response_types=[],
                    scopes=[],
                    contacts=[],
                    token_endpoint_auth_method=TokenEndpointAuthMethod.NONE,
                )
                db.add(client)
                await db.flush()

                svc = OAuth2ClientService(db)
                with pytest.raises(InvalidClientError, match="public"):
                    await svc.rotate_secret("pub-rotate")

        asyncio.run(_run())


# --- deps.py: get_db rollback ---


class TestGetDbRollback:
    """Test get_db exception rollback path."""

    def test_rollback_on_commit_failure(self) -> None:
        """get_db rolls back when commit raises."""
        from shomer.deps import get_db

        async def _run() -> None:
            with patch("shomer.deps.async_session") as mock_factory:
                mock_session = AsyncMock()
                mock_cm = AsyncMock()
                mock_cm.__aenter__.return_value = mock_session
                mock_cm.__aexit__.return_value = False
                mock_factory.return_value = mock_cm
                mock_session.commit.side_effect = RuntimeError("db error")

                with pytest.raises(RuntimeError, match="db error"):
                    async for _s in get_db():
                        pass

                mock_session.rollback.assert_awaited_once()

        asyncio.run(_run())


# --- middleware/session.py: renewal path ---


class TestSessionMiddlewareRenewal:
    """Test middleware session renewal path directly."""

    def test_no_cookie_passes_through(self) -> None:
        """No session cookie — middleware does nothing."""
        from shomer.middleware.session import SessionMiddleware

        async def _run() -> None:
            mock_request = MagicMock()
            mock_request.cookies.get.return_value = None
            mock_response = MagicMock()
            mock_call_next = AsyncMock(return_value=mock_response)

            middleware = SessionMiddleware(app=MagicMock())
            result = await middleware.dispatch(mock_request, mock_call_next)
            assert result == mock_response
            mock_call_next.assert_awaited_once()

        asyncio.run(_run())

    def test_invalid_cookie_passes_through(self) -> None:
        """Invalid session token — middleware passes through."""
        from shomer.middleware.session import SessionMiddleware

        async def _run() -> None:
            mock_svc = AsyncMock()
            mock_svc.validate.return_value = None
            mock_db = AsyncMock()
            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_db
            mock_cm.__aexit__.return_value = False

            mock_request = MagicMock()
            mock_request.cookies.get.return_value = "invalid-tok"
            mock_response = MagicMock()
            mock_call_next = AsyncMock(return_value=mock_response)

            middleware = SessionMiddleware(app=MagicMock())

            with (
                patch(
                    "shomer.middleware.session.async_session",
                    return_value=mock_cm,
                ),
                patch(
                    "shomer.middleware.session.SessionService",
                    return_value=mock_svc,
                ),
            ):
                result = await middleware.dispatch(mock_request, mock_call_next)

            mock_svc.renew.assert_not_awaited()
            assert result == mock_response

        asyncio.run(_run())

    def test_renew_called_for_valid_session(self) -> None:
        """Middleware calls renew() and commit() for valid sessions."""
        from shomer.middleware.session import SessionMiddleware

        async def _run() -> None:
            mock_session = MagicMock()
            mock_svc = AsyncMock()
            mock_svc.validate.return_value = mock_session
            mock_db = AsyncMock()
            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_db
            mock_cm.__aexit__.return_value = False

            mock_request = MagicMock()
            mock_request.cookies.get.return_value = "valid-token"

            mock_response = MagicMock()
            mock_call_next = AsyncMock(return_value=mock_response)

            middleware = SessionMiddleware(app=MagicMock())

            with (
                patch(
                    "shomer.middleware.session.async_session",
                    return_value=mock_cm,
                ),
                patch(
                    "shomer.middleware.session.SessionService",
                    return_value=mock_svc,
                ),
            ):
                result = await middleware.dispatch(mock_request, mock_call_next)

            mock_svc.validate.assert_awaited_once_with("valid-token")
            mock_svc.renew.assert_awaited_once_with(mock_session)
            mock_db.commit.assert_awaited_once()
            assert result == mock_response

        asyncio.run(_run())


# --- services/jwt_service.py: create_access_token with scopes ---


class TestJWTServiceAccessToken:
    """Test JWTService.create_access_token with scopes and extra_claims."""

    def test_create_access_token_with_scopes(self) -> None:
        """create_access_token includes scope claim."""
        from shomer.services.jwt_service import JWTService

        async def _run() -> None:
            mock_settings = MagicMock()
            mock_settings.jwt_issuer = "https://test.local"
            mock_settings.jwt_access_token_exp = 3600
            mock_db = AsyncMock()
            mock_enc = MagicMock()

            svc = JWTService(mock_settings, mock_db, mock_enc)
            with patch.object(svc, "_sign", new_callable=AsyncMock) as mock_sign:
                mock_sign.return_value = "signed-jwt"
                result = await svc.create_access_token(
                    sub="user-1",
                    aud="client-1",
                    scopes=["openid", "profile"],
                    extra_claims={"email": "test@example.com"},
                )
                assert result == "signed-jwt"
                call_kwargs = mock_sign.call_args
                extra = call_kwargs[1].get("extra_claims", {})
                assert extra.get("scope") == "openid profile"
                assert extra.get("email") == "test@example.com"

        asyncio.run(_run())


# --- services/jwt_validation_service.py: error paths ---


class TestJWTValidationErrors:
    """Test JWT validation error handling paths."""

    def test_decode_error(self) -> None:
        """Malformed token returns invalid result."""
        from shomer.services.jwt_validation_service import JWTValidationService

        async def _run() -> None:
            mock_settings = MagicMock()
            mock_settings.jwt_issuer = "https://test.local"
            mock_db = AsyncMock()

            svc = JWTValidationService(mock_settings, mock_db)
            result = await svc.validate("not.a.valid.jwt")
            assert result.valid is False

        asyncio.run(_run())

    def test_invalid_issuer(self) -> None:
        """Token with wrong issuer returns invalid result."""
        from shomer.services.jwt_validation_service import JWTValidationService

        async def _run() -> None:
            mock_settings = MagicMock()
            mock_settings.jwt_issuer = "https://correct.local"
            mock_db = AsyncMock()

            svc = JWTValidationService(mock_settings, mock_db)
            # Malformed enough to trigger DecodeError
            result = await svc.validate("eyJhbGciOiJSUzI1NiJ9.e30.invalid")
            assert result.valid is False

        asyncio.run(_run())

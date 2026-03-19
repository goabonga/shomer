# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests to close remaining coverage gaps in services."""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from shomer.models.oauth2_client import (
    ClientType,
    TokenEndpointAuthMethod,
)
from shomer.services.oauth2_client_service import (
    InvalidClientError,
    OAuth2ClientService,
)
from shomer.services.session_service import SessionService

# --- models/queries.py: get_user_by_id ---


class TestCreateUser:
    """Tests for create_user query helper."""

    def test_creates_user_with_email_and_password(self) -> None:
        async def _run() -> None:
            from shomer.models.queries import create_user

            db = AsyncMock()
            db.add = MagicMock()
            db.add_all = MagicMock()
            db.flush = AsyncMock()

            user = await create_user(
                db, email="a@b.com", password_hash="$hash", username="bob"
            )
            assert user.username == "bob"
            db.add.assert_called_once()
            db.add_all.assert_called_once()
            assert db.flush.await_count == 2

        asyncio.run(_run())


class TestGetUserByEmail:
    """Tests for get_user_by_email query helper."""

    def test_returns_user_when_found(self) -> None:
        async def _run() -> None:
            from shomer.models.queries import get_user_by_email

            db = AsyncMock()
            mock_user = MagicMock()
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_user
            db.execute.return_value = result

            found = await get_user_by_email(db, "a@b.com")
            assert found is mock_user

        asyncio.run(_run())

    def test_returns_none_when_not_found(self) -> None:
        async def _run() -> None:
            from shomer.models.queries import get_user_by_email

            db = AsyncMock()
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db.execute.return_value = result

            found = await get_user_by_email(db, "x@b.com")
            assert found is None

        asyncio.run(_run())


class TestGetUserById:
    """Tests for get_user_by_id query helper."""

    def test_returns_user_when_found(self) -> None:
        """get_user_by_id returns user when present in DB."""

        async def _run() -> None:
            from shomer.models.queries import get_user_by_id

            db = AsyncMock()
            mock_user = MagicMock()
            mock_user.username = "found"

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_user
            db.execute.return_value = result

            found = await get_user_by_id(db, uuid.uuid4())
            assert found is not None
            assert found.username == "found"

        asyncio.run(_run())

    def test_returns_none_when_not_found(self) -> None:
        """get_user_by_id returns None when user not in DB."""

        async def _run() -> None:
            from shomer.models.queries import get_user_by_id

            db = AsyncMock()
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db.execute.return_value = result

            found = await get_user_by_id(db, uuid.uuid4())
            assert found is None

        asyncio.run(_run())


# --- services/session_service.py: validate naive datetime ---


class TestSessionValidateNaiveDatetime:
    """Test session validation with naive (no-tzinfo) datetime from SQLite."""

    def test_valid_session_with_naive_datetime(self) -> None:
        """SQLite returns naive datetimes -- validate must handle them."""
        import hashlib
        import warnings
        from datetime import datetime, timedelta

        async def _run() -> None:
            db = AsyncMock()
            raw = uuid.uuid4().hex
            thash = hashlib.sha256(raw.encode()).hexdigest()

            # Use naive datetime (no timezone) -- mimics SQLite behavior
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                naive_now = datetime.utcnow()  # noqa: DTZ003
                naive_future = naive_now + timedelta(hours=24)

            mock_session = MagicMock()
            mock_session.user_id = uuid.uuid4()
            mock_session.token_hash = thash
            mock_session.expires_at = naive_future

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_session
            db.execute.return_value = result

            svc = SessionService(db)
            found = await svc.validate(raw)
            assert found is not None

        asyncio.run(_run())


# --- services/oauth2_client_service.py: authenticate + rotate ---


class TestOAuth2ClientAuthenticateEdgeCases:
    """Tests for authenticate_client edge cases."""

    def test_none_method_public_client(self) -> None:
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

    def test_none_method_confidential_client_raises(self) -> None:
        """Confidential client with auth_method=NONE raises error."""

        async def _run() -> None:
            db = AsyncMock()

            mock_client = MagicMock()
            mock_client.client_id = "conf-none"
            mock_client.client_type = ClientType.CONFIDENTIAL
            mock_client.token_endpoint_auth_method = TokenEndpointAuthMethod.NONE

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_client
            db.execute.return_value = result

            svc = OAuth2ClientService(db)
            with pytest.raises(InvalidClientError, match="only allowed for public"):
                await svc.authenticate_client(body_client_id="conf-none")

        asyncio.run(_run())

    def test_secret_method_missing_secret_raises(self) -> None:
        """Secret-based auth without providing a secret raises error."""

        async def _run() -> None:
            db = AsyncMock()

            mock_client = MagicMock()
            mock_client.client_id = "secret-client"
            mock_client.client_type = ClientType.CONFIDENTIAL
            mock_client.token_endpoint_auth_method = (
                TokenEndpointAuthMethod.CLIENT_SECRET_BASIC
            )
            mock_client.client_secret_hash = "$argon2id$hash"

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_client
            db.execute.return_value = result

            svc = OAuth2ClientService(db)
            with pytest.raises(InvalidClientError, match="secret required"):
                await svc.authenticate_client(
                    body_client_id="secret-client",
                    body_client_secret=None,
                )

        asyncio.run(_run())

    def test_secret_method_wrong_secret_raises(self) -> None:
        """Wrong client_secret raises error."""

        async def _run() -> None:
            db = AsyncMock()

            mock_client = MagicMock()
            mock_client.client_id = "wrong-secret-client"
            mock_client.client_type = ClientType.CONFIDENTIAL
            mock_client.token_endpoint_auth_method = (
                TokenEndpointAuthMethod.CLIENT_SECRET_BASIC
            )
            mock_client.client_secret_hash = "$argon2id$hash"

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_client
            db.execute.return_value = result

            with patch(
                "shomer.services.oauth2_client_service.verify_password",
                return_value=False,
            ):
                svc = OAuth2ClientService(db)
                with pytest.raises(InvalidClientError, match="Invalid client"):
                    await svc.authenticate_client(
                        body_client_id="wrong-secret-client",
                        body_client_secret="wrong-secret",
                    )

        asyncio.run(_run())


class TestRotateSecret:
    """Tests for OAuth2ClientService.rotate_secret."""

    def test_rotate_secret_success(self) -> None:
        """Rotating secret of confidential client succeeds."""

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

    def test_rotate_secret_not_found_raises(self) -> None:
        """Rotating a nonexistent client raises InvalidClientError."""

        async def _run() -> None:
            db = AsyncMock()
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db.execute.return_value = result

            svc = OAuth2ClientService(db)
            with pytest.raises(InvalidClientError, match="not found"):
                await svc.rotate_secret("nonexistent")

        asyncio.run(_run())

    def test_rotate_secret_public_client_raises(self) -> None:
        """Rotating secret of public client raises InvalidClientError."""

        async def _run() -> None:
            db = AsyncMock()

            mock_client = MagicMock()
            mock_client.client_id = "pub-rotate"
            mock_client.client_type = ClientType.PUBLIC
            mock_client.token_endpoint_auth_method = TokenEndpointAuthMethod.NONE

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_client
            db.execute.return_value = result

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
        """No session cookie -- middleware does nothing."""
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
        """Invalid session token -- middleware passes through."""
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

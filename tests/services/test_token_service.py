# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for TokenService (authorization_code, client_credentials and password grants)."""

from __future__ import annotations

import asyncio
import hashlib
import secrets
import uuid
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from shomer.core.database import Base
from shomer.core.security import hash_password
from shomer.core.settings import Settings
from shomer.models.access_token import AccessToken  # noqa: F401
from shomer.models.authorization_code import AuthorizationCode
from shomer.models.jwk import JWK  # noqa: F401
from shomer.models.oauth2_client import OAuth2Client  # noqa: F401
from shomer.models.password_reset_token import PasswordResetToken  # noqa: F401
from shomer.models.refresh_token import RefreshToken  # noqa: F401
from shomer.models.session import Session  # noqa: F401
from shomer.models.user import User
from shomer.models.user_email import UserEmail
from shomer.models.user_password import UserPassword
from shomer.models.user_profile import UserProfile  # noqa: F401
from shomer.models.verification_code import VerificationCode  # noqa: F401
from shomer.services.token_service import TokenError, TokenResponse, TokenService

_ENGINE = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_SESSION_FACTORY = async_sessionmaker(_ENGINE, expire_on_commit=False)


def _settings() -> Settings:
    return Settings(
        jwt_issuer="https://test.shomer.local",
        jwt_access_token_exp=3600,
        jwt_id_token_exp=3600,
        jwk_encryption_key="test-secret-key-that-is-at-least-32-bytes!",
    )


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


async def _create_auth_code(
    db: Any,
    *,
    client_id: str = "test-client",
    redirect_uri: str = "https://app.example.com/cb",
    scopes: str = "openid profile",
    nonce: str | None = None,
    code_challenge: str | None = None,
    code_challenge_method: str | None = None,
    expired: bool = False,
    used: bool = False,
) -> tuple[str, uuid.UUID]:
    """Create a user + auth code. Returns (code, user_id)."""
    user = User(username="test")
    db.add(user)
    await db.flush()

    code = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    ac = AuthorizationCode(
        code=code,
        user_id=user.id,
        client_id=client_id,
        redirect_uri=redirect_uri,
        scopes=scopes,
        nonce=nonce,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
        expires_at=now - timedelta(hours=1) if expired else now + timedelta(minutes=10),
        is_used=used,
        used_at=now if used else None,
    )
    db.add(ac)
    await db.flush()
    return code, user.id


class TestExchangeAuthorizationCode:
    """Tests for TokenService.exchange_authorization_code()."""

    def test_successful_exchange(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                code, _ = await _create_auth_code(db)
                svc = TokenService(db, _settings())
                resp = await svc.exchange_authorization_code(
                    code=code,
                    client_id="test-client",
                    redirect_uri="https://app.example.com/cb",
                )
                assert resp.access_token is not None
                assert resp.refresh_token is not None
                assert resp.token_type == "Bearer"
                assert resp.scope == "openid profile"

        asyncio.run(_run())

    def test_issues_id_token_with_openid_scope(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                code, _ = await _create_auth_code(
                    db, scopes="openid profile", nonce="abc"
                )
                svc = TokenService(db, _settings())
                resp = await svc.exchange_authorization_code(
                    code=code,
                    client_id="test-client",
                    redirect_uri="https://app.example.com/cb",
                )
                assert resp.id_token is not None

        asyncio.run(_run())

    def test_no_id_token_without_openid(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                code, _ = await _create_auth_code(db, scopes="profile")
                svc = TokenService(db, _settings())
                resp = await svc.exchange_authorization_code(
                    code=code,
                    client_id="test-client",
                    redirect_uri="https://app.example.com/cb",
                )
                assert resp.id_token is None

        asyncio.run(_run())

    def test_invalid_code_raises(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = TokenService(db, _settings())
                with pytest.raises(TokenError, match="Invalid"):
                    await svc.exchange_authorization_code(
                        code="nonexistent",
                        client_id="test-client",
                        redirect_uri="https://app.example.com/cb",
                    )

        asyncio.run(_run())

    def test_expired_code_raises(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                code, _ = await _create_auth_code(db, expired=True)
                svc = TokenService(db, _settings())
                with pytest.raises(TokenError, match="expired"):
                    await svc.exchange_authorization_code(
                        code=code,
                        client_id="test-client",
                        redirect_uri="https://app.example.com/cb",
                    )

        asyncio.run(_run())

    def test_used_code_raises(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                code, _ = await _create_auth_code(db, used=True)
                svc = TokenService(db, _settings())
                with pytest.raises(TokenError, match="already used"):
                    await svc.exchange_authorization_code(
                        code=code,
                        client_id="test-client",
                        redirect_uri="https://app.example.com/cb",
                    )

        asyncio.run(_run())

    def test_client_mismatch_raises(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                code, _ = await _create_auth_code(db)
                svc = TokenService(db, _settings())
                with pytest.raises(TokenError, match="Client mismatch"):
                    await svc.exchange_authorization_code(
                        code=code,
                        client_id="wrong-client",
                        redirect_uri="https://app.example.com/cb",
                    )

        asyncio.run(_run())

    def test_redirect_uri_mismatch_raises(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                code, _ = await _create_auth_code(db)
                svc = TokenService(db, _settings())
                with pytest.raises(TokenError, match="Redirect URI"):
                    await svc.exchange_authorization_code(
                        code=code,
                        client_id="test-client",
                        redirect_uri="https://evil.com/cb",
                    )

        asyncio.run(_run())

    def test_marks_code_as_used(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                code, _ = await _create_auth_code(db)
                svc = TokenService(db, _settings())
                await svc.exchange_authorization_code(
                    code=code,
                    client_id="test-client",
                    redirect_uri="https://app.example.com/cb",
                )
                # Second use should fail
                with pytest.raises(TokenError, match="already used"):
                    await svc.exchange_authorization_code(
                        code=code,
                        client_id="test-client",
                        redirect_uri="https://app.example.com/cb",
                    )

        asyncio.run(_run())


class TestPKCE:
    """Tests for PKCE verification."""

    def test_pkce_s256_success(self) -> None:
        import base64

        verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                code, _ = await _create_auth_code(
                    db, code_challenge=challenge, code_challenge_method="S256"
                )
                svc = TokenService(db, _settings())
                resp = await svc.exchange_authorization_code(
                    code=code,
                    client_id="test-client",
                    redirect_uri="https://app.example.com/cb",
                    code_verifier=verifier,
                )
                assert resp.access_token is not None

        asyncio.run(_run())

    def test_pkce_missing_verifier_raises(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                code, _ = await _create_auth_code(
                    db, code_challenge="challenge", code_challenge_method="S256"
                )
                svc = TokenService(db, _settings())
                with pytest.raises(TokenError, match="code_verifier required"):
                    await svc.exchange_authorization_code(
                        code=code,
                        client_id="test-client",
                        redirect_uri="https://app.example.com/cb",
                    )

        asyncio.run(_run())

    def test_pkce_wrong_verifier_raises(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                code, _ = await _create_auth_code(
                    db, code_challenge="correct-challenge", code_challenge_method="S256"
                )
                svc = TokenService(db, _settings())
                with pytest.raises(TokenError, match="PKCE verification failed"):
                    await svc.exchange_authorization_code(
                        code=code,
                        client_id="test-client",
                        redirect_uri="https://app.example.com/cb",
                        code_verifier="wrong-verifier",
                    )

        asyncio.run(_run())


class TestClientCredentials:
    """Tests for TokenService.issue_client_credentials()."""

    def test_successful_issue(self) -> None:
        """Issue access_token with all allowed scopes."""

        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = TokenService(db, _settings())
                resp = await svc.issue_client_credentials(
                    client_id="m2m-client",
                    client_scopes=["read", "write"],
                )
                assert resp.access_token is not None
                assert resp.token_type == "Bearer"
                assert resp.refresh_token is None
                assert resp.id_token is None
                assert resp.scope == "read write"

        asyncio.run(_run())

    def test_grants_requested_scope_subset(self) -> None:
        """Only requested scopes are granted."""

        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = TokenService(db, _settings())
                resp = await svc.issue_client_credentials(
                    client_id="m2m-client",
                    client_scopes=["read", "write", "admin"],
                    requested_scope="read",
                )
                assert resp.scope == "read"

        asyncio.run(_run())

    def test_grants_all_scopes_when_none_requested(self) -> None:
        """All allowed scopes are granted when no scope is requested."""

        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = TokenService(db, _settings())
                resp = await svc.issue_client_credentials(
                    client_id="m2m-client",
                    client_scopes=["read", "write"],
                )
                assert resp.scope == "read write"

        asyncio.run(_run())

    def test_invalid_scope_raises(self) -> None:
        """Requesting a scope not allowed by the client raises TokenError."""

        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = TokenService(db, _settings())
                with pytest.raises(TokenError, match="Scope not allowed"):
                    await svc.issue_client_credentials(
                        client_id="m2m-client",
                        client_scopes=["read"],
                        requested_scope="read admin",
                    )

        asyncio.run(_run())

    def test_no_refresh_token(self) -> None:
        """client_credentials grant must NOT issue a refresh_token."""

        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = TokenService(db, _settings())
                resp = await svc.issue_client_credentials(
                    client_id="m2m-client",
                    client_scopes=["read"],
                )
                assert resp.refresh_token is None

        asyncio.run(_run())

    def test_no_id_token(self) -> None:
        """client_credentials grant must NOT issue an id_token."""

        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = TokenService(db, _settings())
                resp = await svc.issue_client_credentials(
                    client_id="m2m-client",
                    client_scopes=["openid"],
                    requested_scope="openid",
                )
                assert resp.id_token is None

        asyncio.run(_run())

    def test_access_token_record_has_null_user_id(self) -> None:
        """AccessToken record should have user_id=None for M2M tokens."""

        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = TokenService(db, _settings())
                await svc.issue_client_credentials(
                    client_id="m2m-client",
                    client_scopes=["read"],
                )
                from sqlalchemy import select

                from shomer.models.access_token import AccessToken

                stmt = select(AccessToken).where(AccessToken.client_id == "m2m-client")
                result = await db.execute(stmt)
                record = result.scalar_one()
                assert record.user_id is None
                assert record.client_id == "m2m-client"

        asyncio.run(_run())

    def test_subject_is_client_id(self) -> None:
        """JWT subject claim should be the client_id."""
        import jwt as pyjwt

        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                settings = _settings()
                svc = TokenService(db, settings)
                resp = await svc.issue_client_credentials(
                    client_id="m2m-client",
                    client_scopes=["read"],
                )
                payload = pyjwt.decode(
                    resp.access_token,
                    settings.jwk_encryption_key,
                    algorithms=["HS256"],
                    audience="m2m-client",
                )
                assert payload["sub"] == "m2m-client"
                assert payload["aud"] == "m2m-client"

        asyncio.run(_run())


async def _create_verified_user(
    db: Any,
    *,
    email: str = "user@example.com",
    password: str = "securepassword123",
) -> uuid.UUID:
    """Create a user with verified email and current password. Returns user_id."""
    user = User(username="testuser")
    db.add(user)
    await db.flush()

    user_email = UserEmail(
        user_id=user.id,
        email=email,
        is_primary=True,
        is_verified=True,
    )
    db.add(user_email)

    pw = UserPassword(
        user_id=user.id,
        password_hash=hash_password(password),
    )
    db.add(pw)
    await db.flush()
    return user.id


class TestPasswordGrant:
    """Tests for TokenService.issue_password_grant()."""

    def test_successful_password_grant(self) -> None:
        """Valid email + password returns access_token + refresh_token."""

        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                await _create_verified_user(db)
                svc = TokenService(db, _settings())
                resp = await svc.issue_password_grant(
                    username="user@example.com",
                    password="securepassword123",
                    client_id="test-client",
                )
                assert resp.access_token is not None
                assert resp.refresh_token is not None
                assert resp.token_type == "Bearer"

        asyncio.run(_run())

    def test_password_grant_with_scope(self) -> None:
        """Requested scopes are included in the response."""

        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                await _create_verified_user(db)
                svc = TokenService(db, _settings())
                resp = await svc.issue_password_grant(
                    username="user@example.com",
                    password="securepassword123",
                    client_id="test-client",
                    scope="openid profile",
                )
                assert resp.scope == "openid profile"

        asyncio.run(_run())

    def test_unknown_user_raises(self) -> None:
        """Unknown email returns invalid_grant."""

        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = TokenService(db, _settings())
                with pytest.raises(TokenError, match="Invalid credentials"):
                    await svc.issue_password_grant(
                        username="nobody@example.com",
                        password="anything",
                        client_id="test-client",
                    )

        asyncio.run(_run())

    def test_wrong_password_raises(self) -> None:
        """Wrong password returns invalid_grant."""

        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                await _create_verified_user(db)
                svc = TokenService(db, _settings())
                with pytest.raises(TokenError, match="Invalid credentials"):
                    await svc.issue_password_grant(
                        username="user@example.com",
                        password="wrongpassword",
                        client_id="test-client",
                    )

        asyncio.run(_run())

    def test_unverified_email_raises(self) -> None:
        """Unverified email returns invalid_grant."""

        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                user = User(username="unverified")
                db.add(user)
                await db.flush()
                ue = UserEmail(
                    user_id=user.id,
                    email="unverified@example.com",
                    is_primary=True,
                    is_verified=False,
                )
                db.add(ue)
                pw = UserPassword(
                    user_id=user.id,
                    password_hash=hash_password("securepassword123"),
                )
                db.add(pw)
                await db.flush()

                svc = TokenService(db, _settings())
                with pytest.raises(TokenError, match="Email not verified"):
                    await svc.issue_password_grant(
                        username="unverified@example.com",
                        password="securepassword123",
                        client_id="test-client",
                    )

        asyncio.run(_run())

    def test_subject_is_user_id(self) -> None:
        """JWT sub claim should be the user_id."""
        import jwt as pyjwt

        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                user_id = await _create_verified_user(db)
                settings = _settings()
                svc = TokenService(db, settings)
                resp = await svc.issue_password_grant(
                    username="user@example.com",
                    password="securepassword123",
                    client_id="test-client",
                )
                payload = pyjwt.decode(
                    resp.access_token,
                    settings.jwk_encryption_key,
                    algorithms=["HS256"],
                    audience="test-client",
                )
                assert payload["sub"] == str(user_id)

        asyncio.run(_run())

    def test_no_id_token(self) -> None:
        """password grant does not issue id_token."""

        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                await _create_verified_user(db)
                svc = TokenService(db, _settings())
                resp = await svc.issue_password_grant(
                    username="user@example.com",
                    password="securepassword123",
                    client_id="test-client",
                    scope="openid",
                )
                assert resp.id_token is None

        asyncio.run(_run())


class TestTokenResponse:
    """Tests for TokenResponse.to_dict()."""

    def test_minimal_response(self) -> None:
        """Only access_token, token_type, expires_in when no optional fields."""
        resp = TokenResponse(access_token="tok")
        d = resp.to_dict()
        assert d == {"access_token": "tok", "token_type": "Bearer", "expires_in": 3600}
        assert "refresh_token" not in d
        assert "scope" not in d
        assert "id_token" not in d

    def test_full_response(self) -> None:
        """All fields present when set."""
        resp = TokenResponse(
            access_token="tok",
            refresh_token="ref",
            scope="openid",
            id_token="idt",
        )
        d = resp.to_dict()
        assert d["refresh_token"] == "ref"
        assert d["scope"] == "openid"
        assert d["id_token"] == "idt"

    def test_empty_scope_excluded(self) -> None:
        """Empty scope string is excluded from dict."""
        resp = TokenResponse(access_token="tok", scope="")
        d = resp.to_dict()
        assert "scope" not in d


class TestVerifyPKCEPlain:
    """Tests for PKCE plain method."""

    def test_plain_match(self) -> None:
        assert TokenService._verify_pkce("verifier", "verifier", "plain") is True

    def test_plain_mismatch(self) -> None:
        assert TokenService._verify_pkce("verifier", "wrong", "plain") is False

    def test_unknown_method(self) -> None:
        assert TokenService._verify_pkce("v", "c", "unknown") is False

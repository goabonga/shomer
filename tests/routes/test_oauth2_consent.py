# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Integration tests for POST /oauth2/authorize (consent)."""

from __future__ import annotations

import asyncio
import hashlib
import uuid
from collections.abc import AsyncIterator, Iterator
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from shomer.app import app
from shomer.core.database import Base
from shomer.deps import get_db
from shomer.models.access_token import AccessToken  # noqa: F401
from shomer.models.authorization_code import AuthorizationCode  # noqa: F401
from shomer.models.jwk import JWK  # noqa: F401
from shomer.models.oauth2_client import OAuth2Client  # noqa: F401
from shomer.models.password_reset_token import PasswordResetToken  # noqa: F401
from shomer.models.refresh_token import RefreshToken  # noqa: F401
from shomer.models.session import Session
from shomer.models.user import User
from shomer.models.user_email import UserEmail  # noqa: F401
from shomer.models.user_password import UserPassword  # noqa: F401
from shomer.models.user_profile import UserProfile  # noqa: F401
from shomer.models.verification_code import VerificationCode  # noqa: F401
from shomer.services.oauth2_client_service import OAuth2ClientService

_ENGINE = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_SESSION_FACTORY = async_sessionmaker(_ENGINE, expire_on_commit=False)


async def _override_get_db() -> AsyncIterator[AsyncSession]:
    async with _SESSION_FACTORY() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest.fixture(autouse=True)
def _setup() -> Iterator[None]:
    async def _create() -> None:
        async with _ENGINE.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_create())
    app.dependency_overrides[get_db] = _override_get_db

    with patch("shomer.middleware.session.async_session", _SESSION_FACTORY):
        yield

    app.dependency_overrides.clear()

    async def _drop() -> None:
        async with _ENGINE.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    asyncio.run(_drop())


async def _setup_client_and_session(
    db: AsyncSession,
) -> tuple[str, str, str, uuid.UUID]:
    """Create a user, session, and OAuth2 client. Return (client_id, raw_token, csrf, user_id)."""
    user = User(username="test")
    db.add(user)
    await db.flush()

    raw_token = uuid.uuid4().hex
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    csrf = uuid.uuid4().hex
    now = datetime.now(timezone.utc)

    session = Session(
        user_id=user.id,
        token_hash=token_hash,
        csrf_token=csrf,
        last_activity=now,
        expires_at=now + timedelta(hours=24),
    )
    db.add(session)
    await db.flush()

    svc = OAuth2ClientService(db)
    client, _ = await svc.create_client(
        client_name="Test App",
        redirect_uris=["https://app.example.com/callback"],
        response_types=["code"],
        grant_types=["authorization_code"],
        scopes=["openid", "profile"],
    )
    await db.commit()
    return client.client_id, raw_token, csrf, user.id


class TestConsentApprove:
    """Tests for POST /oauth2/authorize with consent=approve."""

    def test_approve_redirects_with_code(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                cid, raw_token, csrf, _ = await _setup_client_and_session(db)

            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                client.cookies.set("session_id", raw_token)
                resp = await client.post(
                    "/oauth2/authorize",
                    data={
                        "consent": "approve",
                        "csrf_token": csrf,
                        "client_id": cid,
                        "redirect_uri": "https://app.example.com/callback",
                        "response_type": "code",
                        "scope": "openid profile",
                        "state": "xyz123",
                        "nonce": "",
                        "code_challenge": "",
                        "code_challenge_method": "",
                    },
                    follow_redirects=False,
                )
                assert resp.status_code == 302
                location = resp.headers["location"]
                assert "code=" in location
                assert "state=xyz123" in location

        asyncio.run(_run())


class TestConsentDeny:
    """Tests for POST /oauth2/authorize with consent=deny."""

    def test_deny_redirects_with_error(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                cid, raw_token, csrf, _ = await _setup_client_and_session(db)

            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                client.cookies.set("session_id", raw_token)
                resp = await client.post(
                    "/oauth2/authorize",
                    data={
                        "consent": "deny",
                        "csrf_token": csrf,
                        "client_id": cid,
                        "redirect_uri": "https://app.example.com/callback",
                        "response_type": "code",
                        "scope": "openid",
                        "state": "abc",
                        "nonce": "",
                        "code_challenge": "",
                        "code_challenge_method": "",
                    },
                    follow_redirects=False,
                )
                assert resp.status_code == 302
                location = resp.headers["location"]
                assert "error=access_denied" in location
                assert "state=abc" in location

        asyncio.run(_run())


class TestCSRFValidation:
    """Tests for CSRF token validation on consent."""

    def test_wrong_csrf_returns_403(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                cid, raw_token, _, _ = await _setup_client_and_session(db)

            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                client.cookies.set("session_id", raw_token)
                resp = await client.post(
                    "/oauth2/authorize",
                    data={
                        "consent": "approve",
                        "csrf_token": "wrong-csrf-token",
                        "client_id": cid,
                        "redirect_uri": "https://app.example.com/callback",
                        "response_type": "code",
                        "scope": "openid",
                        "state": "abc",
                        "nonce": "",
                        "code_challenge": "",
                        "code_challenge_method": "",
                    },
                    follow_redirects=False,
                )
                assert resp.status_code == 403

        asyncio.run(_run())

    def test_no_session_returns_401(self) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/oauth2/authorize",
                    data={
                        "consent": "approve",
                        "csrf_token": "x",
                        "client_id": "x",
                        "redirect_uri": "https://a.com",
                        "response_type": "code",
                        "scope": "",
                        "state": "abc",
                        "nonce": "",
                        "code_challenge": "",
                        "code_challenge_method": "",
                    },
                    follow_redirects=False,
                )
                assert resp.status_code == 401

        asyncio.run(_run())

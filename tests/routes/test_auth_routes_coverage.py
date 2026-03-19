# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Integration tests for auth routes — coverage for verify, resend, login,
logout, password reset, and password change endpoints."""

from __future__ import annotations

import asyncio
import hashlib
import uuid
from collections.abc import AsyncIterator, Iterator
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from shomer.app import app
from shomer.core.database import Base
from shomer.core.security import hash_password
from shomer.deps import get_db
from shomer.models.access_token import AccessToken  # noqa: F401
from shomer.models.authorization_code import AuthorizationCode  # noqa: F401
from shomer.models.jwk import JWK  # noqa: F401
from shomer.models.oauth2_client import OAuth2Client  # noqa: F401
from shomer.models.password_reset_token import PasswordResetToken
from shomer.models.refresh_token import RefreshToken  # noqa: F401
from shomer.models.session import Session
from shomer.models.user import User
from shomer.models.user_email import UserEmail
from shomer.models.user_password import UserPassword
from shomer.models.user_profile import UserProfile  # noqa: F401
from shomer.models.verification_code import VerificationCode

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


async def _create_verified_user(
    db: AsyncSession,
    email: str = "test@example.com",
    password: str = "securepassword123",
) -> uuid.UUID:
    """Create a verified user. Returns user_id."""
    user = User(username="test")
    db.add(user)
    await db.flush()
    ue = UserEmail(user_id=user.id, email=email, is_primary=True, is_verified=True)
    db.add(ue)
    pw = UserPassword(user_id=user.id, password_hash=hash_password(password))
    db.add(pw)
    await db.flush()
    return user.id


async def _create_session(db: AsyncSession, user_id: uuid.UUID) -> tuple[str, str]:
    """Create a session. Returns (raw_token, csrf_token)."""
    raw_token = uuid.uuid4().hex
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    csrf = uuid.uuid4().hex
    now = datetime.now(timezone.utc)
    session = Session(
        user_id=user_id,
        token_hash=token_hash,
        csrf_token=csrf,
        last_activity=now,
        expires_at=now + timedelta(hours=24),
    )
    db.add(session)
    await db.flush()
    return raw_token, csrf


class TestVerifyEndpoint:
    """Tests for POST /auth/verify."""

    def test_verify_success(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                user = User(username="v")
                db.add(user)
                await db.flush()
                ue = UserEmail(
                    user_id=user.id,
                    email="v@example.com",
                    is_primary=True,
                    is_verified=False,
                )
                db.add(ue)
                vc = VerificationCode(
                    email="v@example.com",
                    code="123456",
                    expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
                )
                db.add(vc)
                await db.commit()

            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/auth/verify",
                    json={"email": "v@example.com", "code": "123456"},
                )
                assert resp.status_code == 200
                assert "verified" in resp.json()["message"].lower()

        asyncio.run(_run())

    def test_verify_invalid_code(self) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/auth/verify",
                    json={"email": "x@example.com", "code": "000000"},
                )
                assert resp.status_code == 400

        asyncio.run(_run())


class TestResendEndpoint:
    """Tests for POST /auth/verify/resend."""

    @patch("shomer.routes.auth.send_email_task")
    def test_resend_success(self, mock_task: MagicMock) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                user = User(username="r")
                db.add(user)
                await db.flush()
                ue = UserEmail(
                    user_id=user.id,
                    email="r@example.com",
                    is_primary=True,
                    is_verified=False,
                )
                db.add(ue)
                await db.commit()

            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/auth/verify/resend",
                    json={"email": "r@example.com"},
                )
                assert resp.status_code == 200
                mock_task.delay.assert_called_once()

        asyncio.run(_run())

    def test_resend_not_found(self) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/auth/verify/resend",
                    json={"email": "nope@example.com"},
                )
                assert resp.status_code == 404

        asyncio.run(_run())


class TestLoginEndpoint:
    """Tests for POST /auth/login."""

    def test_login_success(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                await _create_verified_user(db)
                await db.commit()

            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/auth/login",
                    json={
                        "email": "test@example.com",
                        "password": "securepassword123",
                    },
                )
                assert resp.status_code == 200
                assert "user_id" in resp.json()
                assert "session_id" in resp.headers.get("set-cookie", "")

        asyncio.run(_run())

    def test_login_invalid_credentials(self) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/auth/login",
                    json={"email": "x@example.com", "password": "wrong"},
                )
                assert resp.status_code == 401

        asyncio.run(_run())

    def test_login_unverified_email(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                user = User(username="unv")
                db.add(user)
                await db.flush()
                ue = UserEmail(
                    user_id=user.id,
                    email="unv@example.com",
                    is_primary=True,
                    is_verified=False,
                )
                db.add(ue)
                pw = UserPassword(
                    user_id=user.id,
                    password_hash=hash_password("securepassword123"),
                )
                db.add(pw)
                await db.commit()

            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/auth/login",
                    json={
                        "email": "unv@example.com",
                        "password": "securepassword123",
                    },
                )
                assert resp.status_code == 403

        asyncio.run(_run())


class TestLogoutEndpoint:
    """Tests for POST /auth/logout."""

    def test_logout_with_session(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                uid = await _create_verified_user(db)
                raw_token, _ = await _create_session(db, uid)
                await db.commit()

            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                client.cookies.set("session_id", raw_token)
                resp = await client.post("/auth/logout")
                assert resp.status_code == 200

        asyncio.run(_run())

    def test_logout_all(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                uid = await _create_verified_user(db)
                raw_token, _ = await _create_session(db, uid)
                await db.commit()

            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                client.cookies.set("session_id", raw_token)
                resp = await client.post("/auth/logout", json={"logout_all": True})
                assert resp.status_code == 200

        asyncio.run(_run())


class TestPasswordResetEndpoint:
    """Tests for POST /auth/password/reset."""

    @patch("shomer.routes.auth.send_email_task")
    def test_reset_dispatches_email(self, mock_task: MagicMock) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                await _create_verified_user(db)
                await db.commit()

            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/auth/password/reset",
                    json={"email": "test@example.com"},
                )
                assert resp.status_code == 200
                mock_task.delay.assert_called_once()

        asyncio.run(_run())


class TestPasswordResetVerifyEndpoint:
    """Tests for POST /auth/password/reset-verify."""

    def test_reset_verify_success(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                uid = await _create_verified_user(db)
                prt = PasswordResetToken(
                    user_id=uid,
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
                )
                db.add(prt)
                await db.flush()
                token_str = str(prt.token)
                await db.commit()

            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/auth/password/reset-verify",
                    json={
                        "token": token_str,
                        "new_password": "newstrongpassword1",
                    },
                )
                assert resp.status_code == 200
                assert "reset" in resp.json()["message"].lower()

        asyncio.run(_run())

    def test_reset_verify_malformed_token(self) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/auth/password/reset-verify",
                    json={
                        "token": "not-a-uuid",
                        "new_password": "newstrongpassword1",
                    },
                )
                assert resp.status_code == 400

        asyncio.run(_run())


class TestPasswordChangeEndpoint:
    """Tests for POST /auth/password/change."""

    def test_change_success(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                uid = await _create_verified_user(db)
                raw_token, _ = await _create_session(db, uid)
                await db.commit()

            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                client.cookies.set("session_id", raw_token)
                resp = await client.post(
                    "/auth/password/change",
                    json={
                        "current_password": "securepassword123",
                        "new_password": "newsecurepassword1",
                    },
                )
                assert resp.status_code == 200
                assert "changed" in resp.json()["message"].lower()

        asyncio.run(_run())

    def test_change_wrong_password(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                uid = await _create_verified_user(db)
                raw_token, _ = await _create_session(db, uid)
                await db.commit()

            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                client.cookies.set("session_id", raw_token)
                resp = await client.post(
                    "/auth/password/change",
                    json={
                        "current_password": "wrongpassword",
                        "new_password": "newsecurepassword1",
                    },
                )
                assert resp.status_code == 401

        asyncio.run(_run())

    def test_change_invalid_session(self) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                client.cookies.set("session_id", "invalid-token")
                resp = await client.post(
                    "/auth/password/change",
                    json={
                        "current_password": "x",
                        "new_password": "newsecurepassword1",
                    },
                )
                assert resp.status_code == 401

        asyncio.run(_run())

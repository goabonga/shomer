# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Integration tests for POST /auth/password/change."""

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
from shomer.core.security import hash_password
from shomer.deps import get_db
from shomer.models.access_token import AccessToken  # noqa: F401
from shomer.models.jwk import JWK  # noqa: F401
from shomer.models.password_reset_token import PasswordResetToken  # noqa: F401
from shomer.models.refresh_token import RefreshToken  # noqa: F401
from shomer.models.session import Session
from shomer.models.user import User
from shomer.models.user_email import UserEmail
from shomer.models.user_password import UserPassword
from shomer.models.user_profile import UserProfile  # noqa: F401
from shomer.models.verification_code import VerificationCode  # noqa: F401

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


async def _create_authed_user(db: AsyncSession) -> tuple[str, uuid.UUID]:
    """Create a user with a verified email, password, and session."""
    user = User(username="test")
    db.add(user)
    await db.flush()

    email = UserEmail(
        user_id=user.id, email="user@example.com", is_primary=True, is_verified=True
    )
    pw = UserPassword(user_id=user.id, password_hash=hash_password("oldpassword1"))
    db.add_all([email, pw])
    await db.flush()

    raw_token = uuid.uuid4().hex
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    now = datetime.now(timezone.utc)
    session = Session(
        user_id=user.id,
        token_hash=token_hash,
        csrf_token=uuid.uuid4().hex,
        last_activity=now,
        expires_at=now + timedelta(hours=24),
    )
    db.add(session)
    await db.commit()
    return raw_token, user.id


class TestPasswordChangeEndpoint:
    """Integration tests for POST /auth/password/change."""

    def test_no_session_returns_401(self) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/auth/password/change",
                    json={"current_password": "x", "new_password": "newpassword1"},
                )
                assert resp.status_code == 401

        asyncio.run(_run())

    def test_wrong_current_password_returns_401(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                raw_token, _ = await _create_authed_user(db)

            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                client.cookies.set("session_id", raw_token)
                resp = await client.post(
                    "/auth/password/change",
                    json={
                        "current_password": "wrongpassword",
                        "new_password": "newpassword1",
                    },
                )
                assert resp.status_code == 401
                assert "incorrect" in resp.json()["detail"]

        asyncio.run(_run())

    def test_change_password_success(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                raw_token, user_id = await _create_authed_user(db)

            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                client.cookies.set("session_id", raw_token)
                resp = await client.post(
                    "/auth/password/change",
                    json={
                        "current_password": "oldpassword1",
                        "new_password": "newpassword1",
                    },
                )
                assert resp.status_code == 200
                assert "changed" in resp.json()["message"]

        asyncio.run(_run())

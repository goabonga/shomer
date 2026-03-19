# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Integration tests for POST /auth/logout."""

from __future__ import annotations

import asyncio
import hashlib
import uuid
from collections.abc import AsyncIterator, Iterator
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from shomer.app import app
from shomer.core.database import Base
from shomer.deps import get_db
from shomer.models.access_token import AccessToken  # noqa: F401
from shomer.models.jwk import JWK  # noqa: F401
from shomer.models.password_reset_token import PasswordResetToken  # noqa: F401
from shomer.models.refresh_token import RefreshToken  # noqa: F401
from shomer.models.session import Session
from shomer.models.user import User
from shomer.models.user_password import UserPassword  # noqa: F401
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
    """Create tables and override DB dependency."""

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


async def _create_session(db: AsyncSession) -> tuple[str, uuid.UUID]:
    """Create a user with a session, return (raw_token, user_id)."""
    user = User(username="test")
    db.add(user)
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


class TestLogoutEndpoint:
    """Integration tests for POST /auth/logout."""

    def test_logout_without_session(self) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.post("/auth/logout")
                assert resp.status_code == 200
                assert "Logged out" in resp.json()["message"]

        asyncio.run(_run())

    def test_logout_deletes_session(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                raw_token, user_id = await _create_session(db)

            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                client.cookies.set("session_id", raw_token)
                resp = await client.post("/auth/logout")
                assert resp.status_code == 200

            # Session should be deleted
            async with _SESSION_FACTORY() as db:
                token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
                result = await db.execute(
                    select(Session).where(Session.token_hash == token_hash)
                )
                assert result.scalar_one_or_none() is None

        asyncio.run(_run())

    def test_logout_all_deletes_all_sessions(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                raw_token, user_id = await _create_session(db)
                # Create a second session for same user
                now = datetime.now(timezone.utc)
                s2 = Session(
                    user_id=user_id,
                    token_hash=hashlib.sha256(b"other").hexdigest(),
                    csrf_token=uuid.uuid4().hex,
                    last_activity=now,
                    expires_at=now + timedelta(hours=24),
                )
                db.add(s2)
                await db.commit()

            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                client.cookies.set("session_id", raw_token)
                resp = await client.post("/auth/logout", json={"logout_all": True})
                assert resp.status_code == 200

            # All sessions should be deleted
            async with _SESSION_FACTORY() as db:
                result = await db.execute(
                    select(Session).where(Session.user_id == user_id)
                )
                assert list(result.scalars().all()) == []

        asyncio.run(_run())

    def test_logout_clears_cookies(self) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.post("/auth/logout")
                # Check that Set-Cookie headers clear the cookies
                set_cookies = resp.headers.get_list("set-cookie")
                cookie_names = [c.split("=")[0] for c in set_cookies]
                assert "session_id" in cookie_names
                assert "csrf_token" in cookie_names

        asyncio.run(_run())

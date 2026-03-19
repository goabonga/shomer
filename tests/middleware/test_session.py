# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for sliding session expiration middleware."""

from __future__ import annotations

import asyncio
import hashlib
import uuid
from collections.abc import Iterator
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
from shomer.models.user_email import UserEmail  # noqa: F401
from shomer.models.user_password import UserPassword  # noqa: F401
from shomer.models.user_profile import UserProfile  # noqa: F401
from shomer.models.verification_code import VerificationCode  # noqa: F401

_ENGINE = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_SESSION_FACTORY = async_sessionmaker(_ENGINE, expire_on_commit=False)


async def _override_get_db() -> AsyncSession:  # type: ignore[misc]
    async with _SESSION_FACTORY() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest.fixture(autouse=True)
def _setup() -> Iterator[None]:
    """Create tables, override DB, and patch middleware session factory."""

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


async def _create_user_and_session(
    db: AsyncSession,
) -> tuple[uuid.UUID, str]:
    """Create a user with an active session, return (user_id, raw_token)."""
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
        last_activity=now - timedelta(minutes=10),
        expires_at=now + timedelta(hours=23),
    )
    db.add(session)
    await db.commit()
    return user.id, raw_token


class TestSessionMiddleware:
    """Tests for sliding session expiration middleware."""

    def test_unauthenticated_request_passes_through(self) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.get("/liveness")
                assert resp.status_code == 200

        asyncio.run(_run())

    def test_invalid_cookie_passes_through(self) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.get(
                    "/liveness", cookies={"session_id": "invalid-token"}
                )
                assert resp.status_code == 200

        asyncio.run(_run())

    def test_valid_session_gets_renewed(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                user_id, raw_token = await _create_user_and_session(db)

                # Get session before request
                token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
                result = await db.execute(
                    select(Session).where(Session.token_hash == token_hash)
                )
                session_before = result.scalar_one()
                old_last_activity = session_before.last_activity

            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.get("/liveness", cookies={"session_id": raw_token})
                assert resp.status_code == 200

            # Check session was renewed
            async with _SESSION_FACTORY() as db:
                result = await db.execute(
                    select(Session).where(Session.token_hash == token_hash)
                )
                session_after = result.scalar_one()
                # last_activity should have been updated
                assert session_after.last_activity != old_last_activity

        asyncio.run(_run())

    def test_expired_session_not_renewed(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
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
                    last_activity=now - timedelta(hours=25),
                    expires_at=now - timedelta(hours=1),
                )
                db.add(session)
                await db.commit()

            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.get("/liveness", cookies={"session_id": raw_token})
                # Should still pass through (middleware doesn't block)
                assert resp.status_code == 200

        asyncio.run(_run())

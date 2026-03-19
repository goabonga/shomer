# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for SessionService."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from shomer.core.database import Base
from shomer.models.access_token import AccessToken  # noqa: F401
from shomer.models.jwk import JWK  # noqa: F401
from shomer.models.password_reset_token import PasswordResetToken  # noqa: F401
from shomer.models.refresh_token import RefreshToken  # noqa: F401
from shomer.models.user import User
from shomer.models.user_email import UserEmail  # noqa: F401
from shomer.models.user_password import UserPassword  # noqa: F401
from shomer.models.user_profile import UserProfile  # noqa: F401
from shomer.models.verification_code import VerificationCode  # noqa: F401
from shomer.services.session_service import SessionService

_ENGINE = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_SESSION_FACTORY = async_sessionmaker(_ENGINE, expire_on_commit=False)


@pytest.fixture(autouse=True)
def _setup_db() -> Iterator[None]:
    """Create and drop tables for each test."""

    async def _create() -> None:
        async with _ENGINE.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_create())
    yield

    async def _drop() -> None:
        async with _ENGINE.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    asyncio.run(_drop())


async def _create_user(db: AsyncSession) -> uuid.UUID:
    """Insert a minimal user and return its ID."""
    user = User(username="test")
    db.add(user)
    await db.flush()
    assert user.id is not None
    return user.id


class TestCreate:
    """Tests for SessionService.create()."""

    def test_creates_session(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                uid = await _create_user(db)
                svc = SessionService(db)
                session, raw_token = await svc.create(user_id=uid)
                assert session.user_id == uid
                assert session.token_hash is not None
                assert session.csrf_token is not None
                assert len(raw_token) == 32

        asyncio.run(_run())

    def test_stores_metadata(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                uid = await _create_user(db)
                svc = SessionService(db)
                session, _ = await svc.create(
                    user_id=uid,
                    user_agent="Mozilla/5.0",
                    ip_address="10.0.0.1",
                )
                assert session.user_agent == "Mozilla/5.0"
                assert session.ip_address == "10.0.0.1"

        asyncio.run(_run())

    def test_sets_expiration(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                uid = await _create_user(db)
                svc = SessionService(db)
                session, _ = await svc.create(user_id=uid)
                assert session.expires_at > datetime.now(timezone.utc)

        asyncio.run(_run())


class TestValidate:
    """Tests for SessionService.validate()."""

    def test_valid_token(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                uid = await _create_user(db)
                svc = SessionService(db)
                _, raw_token = await svc.create(user_id=uid)
                result = await svc.validate(raw_token)
                assert result is not None
                assert result.user_id == uid

        asyncio.run(_run())

    def test_invalid_token_returns_none(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = SessionService(db)
                result = await svc.validate("nonexistent-token")
                assert result is None

        asyncio.run(_run())

    def test_expired_session_returns_none(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                uid = await _create_user(db)
                svc = SessionService(db)
                session, raw_token = await svc.create(user_id=uid)
                # Manually expire
                session.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
                await db.flush()
                result = await svc.validate(raw_token)
                assert result is None

        asyncio.run(_run())


class TestRenew:
    """Tests for SessionService.renew()."""

    def test_extends_expiration(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                uid = await _create_user(db)
                svc = SessionService(db)
                session, _ = await svc.create(user_id=uid)
                renewed = await svc.renew(session)
                assert renewed.last_activity is not None
                assert renewed.expires_at is not None

        asyncio.run(_run())


class TestDelete:
    """Tests for SessionService.delete()."""

    def test_deletes_session(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                uid = await _create_user(db)
                svc = SessionService(db)
                session, raw_token = await svc.create(user_id=uid)
                deleted = await svc.delete(session.id)
                assert deleted is True
                result = await svc.validate(raw_token)
                assert result is None

        asyncio.run(_run())

    def test_delete_nonexistent_returns_false(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = SessionService(db)
                deleted = await svc.delete(uuid.uuid4())
                assert deleted is False

        asyncio.run(_run())


class TestDeleteAllForUser:
    """Tests for SessionService.delete_all_for_user()."""

    def test_deletes_all_user_sessions(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                uid = await _create_user(db)
                svc = SessionService(db)
                await svc.create(user_id=uid)
                await svc.create(user_id=uid)
                await svc.create(user_id=uid)
                count = await svc.delete_all_for_user(uid)
                assert count == 3

        asyncio.run(_run())

    def test_does_not_delete_other_users(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                uid1 = await _create_user(db)
                uid2 = await _create_user(db)
                svc = SessionService(db)
                await svc.create(user_id=uid1)
                _, token2 = await svc.create(user_id=uid2)
                await svc.delete_all_for_user(uid1)
                result = await svc.validate(token2)
                assert result is not None

        asyncio.run(_run())


class TestListActive:
    """Tests for SessionService.list_active()."""

    def test_lists_active_sessions(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                uid = await _create_user(db)
                svc = SessionService(db)
                await svc.create(user_id=uid)
                await svc.create(user_id=uid)
                sessions = await svc.list_active(uid)
                assert len(sessions) == 2

        asyncio.run(_run())

    def test_excludes_expired(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                uid = await _create_user(db)
                svc = SessionService(db)
                session, _ = await svc.create(user_id=uid)
                session.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
                await db.flush()
                await svc.create(user_id=uid)
                sessions = await svc.list_active(uid)
                assert len(sessions) == 1

        asyncio.run(_run())

    def test_empty_for_unknown_user(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as db:
                svc = SessionService(db)
                sessions = await svc.list_active(uuid.uuid4())
                assert sessions == []

        asyncio.run(_run())

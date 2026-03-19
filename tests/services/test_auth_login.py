# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for AuthService login method."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from shomer.core.database import Base
from shomer.models.access_token import AccessToken  # noqa: F401
from shomer.models.jwk import JWK  # noqa: F401
from shomer.models.password_reset_token import PasswordResetToken  # noqa: F401
from shomer.models.refresh_token import RefreshToken  # noqa: F401
from shomer.models.session import Session
from shomer.models.user import User  # noqa: F401
from shomer.models.user_email import UserEmail
from shomer.models.user_password import UserPassword  # noqa: F401
from shomer.models.user_profile import UserProfile  # noqa: F401
from shomer.models.verification_code import VerificationCode  # noqa: F401
from shomer.services.auth_service import (
    AuthService,
    EmailNotVerifiedError,
    InvalidCredentialsError,
)

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


async def _register_and_verify(
    session: AsyncSession, email: str, password: str
) -> None:
    """Helper: register a user and mark email as verified."""
    svc = AuthService(session)
    await svc.register(email=email, password=password)
    # Mark email as verified
    result = await session.execute(select(UserEmail).where(UserEmail.email == email))
    ue = result.scalar_one()
    ue.is_verified = True
    await session.flush()


class TestLogin:
    """Tests for AuthService.login()."""

    def test_login_success(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                await _register_and_verify(
                    session, "user@example.com", "securepassword"
                )
                svc = AuthService(session)
                user, sess, _ = await svc.login(
                    email="user@example.com", password="securepassword"
                )
                assert user.id is not None
                assert sess.token_hash is not None
                assert sess.csrf_token is not None

        asyncio.run(_run())

    def test_login_creates_session(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                await _register_and_verify(
                    session, "user@example.com", "securepassword"
                )
                svc = AuthService(session)
                _, sess, _ = await svc.login(
                    email="user@example.com", password="securepassword"
                )
                result = await session.execute(
                    select(Session).where(Session.id == sess.id)
                )
                db_session = result.scalar_one()
                assert db_session.user_id is not None

        asyncio.run(_run())

    def test_login_stores_user_agent_and_ip(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                await _register_and_verify(
                    session, "user@example.com", "securepassword"
                )
                svc = AuthService(session)
                _, sess, _ = await svc.login(
                    email="user@example.com",
                    password="securepassword",
                    user_agent="Mozilla/5.0",
                    ip_address="192.168.1.1",
                )
                assert sess.user_agent == "Mozilla/5.0"
                assert sess.ip_address == "192.168.1.1"

        asyncio.run(_run())

    def test_wrong_password_raises(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                await _register_and_verify(
                    session, "user@example.com", "securepassword"
                )
                svc = AuthService(session)
                with pytest.raises(InvalidCredentialsError):
                    await svc.login(email="user@example.com", password="wrong")

        asyncio.run(_run())

    def test_unknown_email_raises(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = AuthService(session)
                with pytest.raises(InvalidCredentialsError):
                    await svc.login(email="nobody@example.com", password="pass")

        asyncio.run(_run())

    def test_unverified_email_raises(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = AuthService(session)
                await svc.register(
                    email="unverified@example.com", password="securepassword"
                )
                with pytest.raises(EmailNotVerifiedError):
                    await svc.login(
                        email="unverified@example.com", password="securepassword"
                    )

        asyncio.run(_run())

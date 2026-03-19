# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for AuthService password reset methods."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from shomer.core.database import Base
from shomer.core.security import verify_password
from shomer.models.access_token import AccessToken  # noqa: F401
from shomer.models.jwk import JWK  # noqa: F401
from shomer.models.password_reset_token import PasswordResetToken
from shomer.models.refresh_token import RefreshToken  # noqa: F401
from shomer.models.session import Session  # noqa: F401
from shomer.models.user import User  # noqa: F401
from shomer.models.user_email import UserEmail  # noqa: F401
from shomer.models.user_password import UserPassword
from shomer.models.user_profile import UserProfile  # noqa: F401
from shomer.models.verification_code import VerificationCode  # noqa: F401
from shomer.services.auth_service import AuthService, InvalidResetTokenError

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


class TestRequestPasswordReset:
    """Tests for AuthService.request_password_reset()."""

    def test_returns_token_for_existing_user(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = AuthService(session)
                await svc.register(email="user@example.com", password="securepassword")
                token = await svc.request_password_reset(email="user@example.com")
                assert token is not None
                assert isinstance(token, uuid.UUID)

        asyncio.run(_run())

    def test_returns_none_for_unknown_email(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = AuthService(session)
                token = await svc.request_password_reset(email="nobody@example.com")
                assert token is None

        asyncio.run(_run())

    def test_creates_token_in_db(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = AuthService(session)
                await svc.register(email="user@example.com", password="securepassword")
                token = await svc.request_password_reset(email="user@example.com")

                result = await session.execute(
                    select(PasswordResetToken).where(PasswordResetToken.token == token)
                )
                prt = result.scalar_one()
                assert prt.used is False

        asyncio.run(_run())


class TestVerifyPasswordReset:
    """Tests for AuthService.verify_password_reset()."""

    def test_resets_password(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = AuthService(session)
                await svc.register(email="user@example.com", password="oldpassword1")
                token = await svc.request_password_reset(email="user@example.com")
                assert token is not None
                await svc.verify_password_reset(
                    token=token, new_password="newpassword1"
                )

                # Verify new password works
                result = await session.execute(
                    select(UserPassword).where(
                        UserPassword.is_current == True  # noqa: E712
                    )
                )
                pw = result.scalar_one()
                assert verify_password("newpassword1", pw.password_hash)

        asyncio.run(_run())

    def test_marks_token_as_used(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = AuthService(session)
                await svc.register(email="user@example.com", password="oldpassword1")
                token = await svc.request_password_reset(email="user@example.com")
                assert token is not None
                await svc.verify_password_reset(
                    token=token, new_password="newpassword1"
                )

                result = await session.execute(
                    select(PasswordResetToken).where(PasswordResetToken.token == token)
                )
                prt = result.scalar_one()
                assert prt.used is True

        asyncio.run(_run())

    def test_reuse_raises(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = AuthService(session)
                await svc.register(email="user@example.com", password="oldpassword1")
                token = await svc.request_password_reset(email="user@example.com")
                assert token is not None
                await svc.verify_password_reset(
                    token=token, new_password="newpassword1"
                )
                with pytest.raises(InvalidResetTokenError):
                    await svc.verify_password_reset(
                        token=token, new_password="anotherpassword"
                    )

        asyncio.run(_run())

    def test_expired_token_raises(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = AuthService(session)
                await svc.register(email="user@example.com", password="oldpassword1")
                token = await svc.request_password_reset(email="user@example.com")
                assert token is not None

                # Expire the token
                result = await session.execute(
                    select(PasswordResetToken).where(PasswordResetToken.token == token)
                )
                prt = result.scalar_one()
                prt.expires_at = datetime.now(timezone.utc) - timedelta(hours=2)
                await session.flush()

                with pytest.raises(InvalidResetTokenError):
                    await svc.verify_password_reset(
                        token=token, new_password="newpassword1"
                    )

        asyncio.run(_run())

    def test_invalid_token_raises(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = AuthService(session)
                with pytest.raises(InvalidResetTokenError):
                    await svc.verify_password_reset(
                        token=uuid.uuid4(), new_password="newpassword1"
                    )

        asyncio.run(_run())

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for AuthService verify and resend methods."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from shomer.core.database import Base
from shomer.models.access_token import AccessToken  # noqa: F401
from shomer.models.jwk import JWK  # noqa: F401
from shomer.models.password_reset_token import PasswordResetToken  # noqa: F401
from shomer.models.refresh_token import RefreshToken  # noqa: F401
from shomer.models.session import Session  # noqa: F401
from shomer.models.user import User  # noqa: F401
from shomer.models.user_email import UserEmail
from shomer.models.user_password import UserPassword  # noqa: F401
from shomer.models.user_profile import UserProfile  # noqa: F401
from shomer.models.verification_code import VerificationCode
from shomer.services.auth_service import (
    AuthService,
    EmailNotFoundError,
    InvalidCodeError,
    RateLimitError,
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


class TestVerifyEmail:
    """Tests for AuthService.verify_email()."""

    def test_valid_code_verifies_email(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = AuthService(session)
                _, code = await svc.register(
                    email="test@example.com", password="securepassword"
                )
                await svc.verify_email(email="test@example.com", code=code)

                result = await session.execute(
                    select(UserEmail).where(UserEmail.email == "test@example.com")
                )
                ue = result.scalar_one()
                assert ue.is_verified is True
                assert ue.verified_at is not None

        asyncio.run(_run())

    def test_code_marked_as_used(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = AuthService(session)
                _, code = await svc.register(
                    email="test@example.com", password="securepassword"
                )
                await svc.verify_email(email="test@example.com", code=code)

                result = await session.execute(
                    select(VerificationCode).where(
                        VerificationCode.email == "test@example.com"
                    )
                )
                vc = result.scalar_one()
                assert vc.used is True

        asyncio.run(_run())

    def test_wrong_code_raises(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = AuthService(session)
                await svc.register(email="test@example.com", password="securepassword")
                with pytest.raises(InvalidCodeError):
                    await svc.verify_email(email="test@example.com", code="999999")

        asyncio.run(_run())

    def test_expired_code_raises(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = AuthService(session)
                await svc.register(email="test@example.com", password="securepassword")
                # Manually expire the code
                result = await session.execute(
                    select(VerificationCode).where(
                        VerificationCode.email == "test@example.com"
                    )
                )
                vc = result.scalar_one()
                vc.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
                await session.flush()

                with pytest.raises(InvalidCodeError):
                    await svc.verify_email(email="test@example.com", code=vc.code)

        asyncio.run(_run())

    def test_used_code_raises(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = AuthService(session)
                _, code = await svc.register(
                    email="test@example.com", password="securepassword"
                )
                await svc.verify_email(email="test@example.com", code=code)
                with pytest.raises(InvalidCodeError):
                    await svc.verify_email(email="test@example.com", code=code)

        asyncio.run(_run())


class TestResendCode:
    """Tests for AuthService.resend_code()."""

    def test_resend_generates_new_code(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = AuthService(session)
                await svc.register(email="test@example.com", password="securepassword")
                # Expire the first code's created_at to bypass rate limit
                result = await session.execute(
                    select(VerificationCode).where(
                        VerificationCode.email == "test@example.com"
                    )
                )
                vc = result.scalar_one()
                vc.created_at = datetime.now(timezone.utc) - timedelta(minutes=5)
                await session.flush()

                new_code = await svc.resend_code(email="test@example.com")
                assert len(new_code) == 6
                assert new_code.isdigit()

        asyncio.run(_run())

    def test_resend_unknown_email_raises(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = AuthService(session)
                with pytest.raises(EmailNotFoundError):
                    await svc.resend_code(email="unknown@example.com")

        asyncio.run(_run())

    def test_resend_rate_limit(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = AuthService(session)
                await svc.register(email="test@example.com", password="securepassword")
                # The registration just created a code, so resend should be rate limited
                with pytest.raises(RateLimitError):
                    await svc.resend_code(email="test@example.com")

        asyncio.run(_run())

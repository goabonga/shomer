# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for AuthService (registration)."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from shomer.core.database import Base
from shomer.models.access_token import AccessToken  # noqa: F401
from shomer.models.jwk import JWK  # noqa: F401
from shomer.models.password_reset_token import PasswordResetToken  # noqa: F401
from shomer.models.refresh_token import RefreshToken  # noqa: F401
from shomer.models.session import Session  # noqa: F401
from shomer.models.user import User  # noqa: F401
from shomer.models.user_email import UserEmail  # noqa: F401
from shomer.models.user_password import UserPassword  # noqa: F401
from shomer.models.user_profile import UserProfile  # noqa: F401
from shomer.models.verification_code import VerificationCode  # noqa: F401
from shomer.services.auth_service import AuthService, DuplicateEmailError

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


class TestRegister:
    """Tests for AuthService.register()."""

    def test_creates_user(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = AuthService(session)
                user, code = await svc.register(
                    email="test@example.com",
                    password="securepassword",
                )
                assert user.id is not None
                assert len(code) == 6
                assert code.isdigit()

        asyncio.run(_run())

    def test_creates_with_username(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = AuthService(session)
                user, _ = await svc.register(
                    email="test@example.com",
                    password="securepassword",
                    username="testuser",
                )
                assert user.username == "testuser"

        asyncio.run(_run())

    def test_hashes_password(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = AuthService(session)
                await svc.register(
                    email="test@example.com",
                    password="securepassword",
                )
                # Verify password was hashed (not stored plaintext)
                from sqlalchemy import select

                result = await session.execute(select(UserPassword))
                pw = result.scalar_one()
                assert pw.password_hash.startswith("$argon2id$")
                assert pw.password_hash != "securepassword"

        asyncio.run(_run())

    def test_creates_verification_code(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = AuthService(session)
                await svc.register(
                    email="test@example.com",
                    password="securepassword",
                )
                from sqlalchemy import select

                result = await session.execute(
                    select(VerificationCode).where(
                        VerificationCode.email == "test@example.com"
                    )
                )
                vc = result.scalar_one()
                assert vc.code is not None
                assert len(vc.code) == 6
                assert vc.used is False

        asyncio.run(_run())

    def test_duplicate_email_raises(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = AuthService(session)
                await svc.register(
                    email="dupe@example.com",
                    password="securepassword",
                )
                with pytest.raises(DuplicateEmailError):
                    await svc.register(
                        email="dupe@example.com",
                        password="anotherpassword",
                    )

        asyncio.run(_run())

    def test_email_is_primary(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = AuthService(session)
                await svc.register(
                    email="primary@example.com",
                    password="securepassword",
                )
                from sqlalchemy import select

                result = await session.execute(
                    select(UserEmail).where(UserEmail.email == "primary@example.com")
                )
                ue = result.scalar_one()
                assert ue.is_primary is True

        asyncio.run(_run())


class TestGenerateCode:
    """Tests for AuthService._generate_code()."""

    def test_code_is_6_digits(self) -> None:
        code = AuthService._generate_code()
        assert len(code) == 6
        assert code.isdigit()

    def test_codes_are_different(self) -> None:
        codes = {AuthService._generate_code() for _ in range(100)}
        assert len(codes) > 1

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for RSA key management service."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Iterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from shomer.core.database import Base
from shomer.core.security import AESEncryption
from shomer.models.jwk import JWKStatus
from shomer.models.password_reset_token import PasswordResetToken  # noqa: F401
from shomer.models.session import Session  # noqa: F401

# Import all models so Base.metadata knows every table
from shomer.models.user import User  # noqa: F401
from shomer.models.user_email import UserEmail  # noqa: F401
from shomer.models.user_password import UserPassword  # noqa: F401
from shomer.models.user_profile import UserProfile  # noqa: F401
from shomer.models.verification_code import VerificationCode  # noqa: F401
from shomer.services.jwk_service import JWKService

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
    asyncio.run(_drop())


async def _drop() -> None:
    async with _ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def _make_service(session: AsyncSession, *, key_size: int = 2048) -> JWKService:
    key = AESEncryption.generate_key()
    enc = AESEncryption(key)
    return JWKService(session, enc, key_size=key_size)


class TestGenerateKey:
    """Tests for JWKService.generate_key()."""

    def test_creates_active_key(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = _make_service(session)
                jwk = await svc.generate_key()
                assert jwk.status == JWKStatus.ACTIVE
                assert jwk.kid.startswith("shomer-")
                assert jwk.algorithm == "RS256"

        asyncio.run(_run())

    def test_public_key_is_valid_jwk_json(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = _make_service(session)
                jwk = await svc.generate_key()
                pub = json.loads(jwk.public_key)
                assert pub["kty"] == "RSA"
                assert pub["use"] == "sig"
                assert "n" in pub
                assert "e" in pub

        asyncio.run(_run())

    def test_private_key_is_encrypted(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                key = AESEncryption.generate_key()
                enc = AESEncryption(key)
                svc = JWKService(session, enc)
                jwk = await svc.generate_key()
                # Decrypting with same key should yield PEM
                dec = AESEncryption(key)
                plaintext = dec.decrypt(jwk.private_key_enc)
                assert b"BEGIN PRIVATE KEY" in plaintext

        asyncio.run(_run())

    def test_rotates_existing_active_key(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = _make_service(session)
                first = await svc.generate_key()
                first_kid = first.kid
                await svc.generate_key()
                await session.flush()

                # Refresh first key from DB
                await session.refresh(first)
                assert first.status == JWKStatus.ROTATED

                # New key should be active
                active = await svc.get_active_signing_key()
                assert active is not None
                assert active.kid != first_kid

        asyncio.run(_run())


class TestRotate:
    """Tests for JWKService.rotate()."""

    def test_rotate_returns_new_active(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = _make_service(session)
                await svc.generate_key()
                new_key = await svc.rotate()
                assert new_key.status == JWKStatus.ACTIVE

        asyncio.run(_run())


class TestRevoke:
    """Tests for JWKService.revoke()."""

    def test_revoke_existing_key(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = _make_service(session)
                jwk = await svc.generate_key()
                revoked = await svc.revoke(jwk.kid)
                assert revoked is not None
                assert revoked.status == JWKStatus.REVOKED

        asyncio.run(_run())

    def test_revoke_nonexistent_returns_none(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = _make_service(session)
                result = await svc.revoke("nonexistent-kid")
                assert result is None

        asyncio.run(_run())


class TestGetActiveSigningKey:
    """Tests for JWKService.get_active_signing_key()."""

    def test_returns_none_when_no_keys(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = _make_service(session)
                result = await svc.get_active_signing_key()
                assert result is None

        asyncio.run(_run())

    def test_returns_active_key(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = _make_service(session)
                jwk = await svc.generate_key()
                result = await svc.get_active_signing_key()
                assert result is not None
                assert result.kid == jwk.kid

        asyncio.run(_run())


class TestGetPublicKeys:
    """Tests for JWKService.get_public_keys()."""

    def test_returns_active_and_rotated(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = _make_service(session)
                await svc.generate_key()  # will be rotated
                await svc.generate_key()  # active
                keys = await svc.get_public_keys()
                assert len(keys) == 2

        asyncio.run(_run())

    def test_excludes_revoked(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = _make_service(session)
                jwk = await svc.generate_key()
                await svc.revoke(jwk.kid)
                keys = await svc.get_public_keys()
                assert len(keys) == 0

        asyncio.run(_run())

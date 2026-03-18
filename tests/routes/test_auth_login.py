# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Integration tests for POST /auth/login."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterator
from unittest.mock import MagicMock, patch

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
from shomer.models.session import Session  # noqa: F401
from shomer.models.user import User  # noqa: F401
from shomer.models.user_email import UserEmail
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
    yield
    app.dependency_overrides.clear()

    async def _drop() -> None:
        async with _ENGINE.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    asyncio.run(_drop())


async def _register_and_verify(client: AsyncClient, email: str, password: str) -> None:
    """Register a user and mark their email as verified in the DB."""
    await client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    # Mark email as verified directly in DB
    async with _SESSION_FACTORY() as session:
        result = await session.execute(
            select(UserEmail).where(UserEmail.email == email)
        )
        ue = result.scalar_one()
        ue.is_verified = True
        await session.commit()


class TestLoginEndpoint:
    """Integration tests for POST /auth/login."""

    @patch("shomer.routes.auth.send_email_task")
    def test_login_success(self, mock_task: MagicMock) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                await _register_and_verify(
                    client, "login@example.com", "securepassword"
                )
                resp = await client.post(
                    "/auth/login",
                    json={"email": "login@example.com", "password": "securepassword"},
                )
                assert resp.status_code == 200
                assert "user_id" in resp.json()
                assert "session_id" in resp.cookies
                assert "csrf_token" in resp.cookies

        asyncio.run(_run())

    def test_login_invalid_credentials(self) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/auth/login",
                    json={"email": "nobody@example.com", "password": "wrong"},
                )
                assert resp.status_code == 401
                assert "Invalid" in resp.json()["detail"]

        asyncio.run(_run())

    @patch("shomer.routes.auth.send_email_task")
    def test_login_unverified_email(self, mock_task: MagicMock) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                # Register but do NOT verify
                await client.post(
                    "/auth/register",
                    json={
                        "email": "unverified@example.com",
                        "password": "securepassword",
                    },
                )
                resp = await client.post(
                    "/auth/login",
                    json={
                        "email": "unverified@example.com",
                        "password": "securepassword",
                    },
                )
                assert resp.status_code == 403
                assert "not verified" in resp.json()["detail"]

        asyncio.run(_run())

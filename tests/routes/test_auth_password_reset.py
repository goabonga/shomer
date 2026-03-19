# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Integration tests for password reset endpoints."""

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
from shomer.models.password_reset_token import PasswordResetToken
from shomer.models.refresh_token import RefreshToken  # noqa: F401
from shomer.models.session import Session  # noqa: F401
from shomer.models.user import User  # noqa: F401
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


class TestPasswordResetEndpoint:
    """Tests for POST /auth/password/reset."""

    @patch("shomer.routes.auth.send_email_task")
    def test_request_reset_always_200(self, mock_task: MagicMock) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/auth/password/reset",
                    json={"email": "nobody@example.com"},
                )
                assert resp.status_code == 200
                assert "reset link" in resp.json()["message"]

        asyncio.run(_run())

    @patch("shomer.routes.auth.send_email_task")
    def test_request_reset_sends_email_for_existing(self, mock_task: MagicMock) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                # Register first
                await client.post(
                    "/auth/register",
                    json={"email": "user@example.com", "password": "securepassword"},
                )
                resp = await client.post(
                    "/auth/password/reset",
                    json={"email": "user@example.com"},
                )
                assert resp.status_code == 200
                # Email should be dispatched (register + reset = 2 calls)
                assert mock_task.delay.call_count == 2

        asyncio.run(_run())


class TestPasswordResetVerifyEndpoint:
    """Tests for POST /auth/password/reset-verify."""

    def test_invalid_token_returns_400(self) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/auth/password/reset-verify",
                    json={
                        "token": "00000000-0000-0000-0000-000000000000",
                        "new_password": "newstrongpassword",
                    },
                )
                assert resp.status_code == 400

        asyncio.run(_run())

    def test_malformed_token_returns_400(self) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/auth/password/reset-verify",
                    json={"token": "not-a-uuid", "new_password": "newstrongpassword"},
                )
                assert resp.status_code == 400

        asyncio.run(_run())

    @patch("shomer.routes.auth.send_email_task")
    def test_valid_token_resets_password(self, mock_task: MagicMock) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                # Register
                await client.post(
                    "/auth/register",
                    json={"email": "reset@example.com", "password": "oldpassword1"},
                )
                # Request reset
                await client.post(
                    "/auth/password/reset",
                    json={"email": "reset@example.com"},
                )

                # Get token from DB
                async with _SESSION_FACTORY() as db:
                    result = await db.execute(select(PasswordResetToken))
                    prt = result.scalar_one()
                    token_str = str(prt.token)

                resp = await client.post(
                    "/auth/password/reset-verify",
                    json={"token": token_str, "new_password": "newpassword1"},
                )
                assert resp.status_code == 200
                assert "reset successfully" in resp.json()["message"]

        asyncio.run(_run())

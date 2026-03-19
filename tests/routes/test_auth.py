# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Integration tests for POST /auth/register."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
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


async def _override_get_db() -> AsyncIterator[AsyncMock]:
    async with _SESSION_FACTORY() as session:
        try:
            yield session  # type: ignore[misc]
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest.fixture(autouse=True)
def _setup(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
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


class TestRegisterEndpoint:
    """Integration tests for POST /auth/register."""

    @patch("shomer.routes.auth.send_email_task")
    def test_register_success(self, mock_task: MagicMock) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/auth/register",
                    json={
                        "email": "new@example.com",
                        "password": "strongpassword",
                    },
                )
                assert resp.status_code == 201
                body = resp.json()
                assert body["message"] is not None
                assert "user_id" in body
                mock_task.delay.assert_called_once()

        asyncio.run(_run())

    @patch("shomer.routes.auth.send_email_task")
    def test_register_duplicate_email(self, mock_task: MagicMock) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                await client.post(
                    "/auth/register",
                    json={
                        "email": "dupe@example.com",
                        "password": "strongpassword",
                    },
                )
                resp = await client.post(
                    "/auth/register",
                    json={
                        "email": "dupe@example.com",
                        "password": "anotherpassword",
                    },
                )
                assert resp.status_code == 201
                assert "Registration successful" in resp.json()["message"]

        asyncio.run(_run())

    def test_register_weak_password(self) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/auth/register",
                    json={
                        "email": "weak@example.com",
                        "password": "short",
                    },
                )
                assert resp.status_code == 422

        asyncio.run(_run())

    def test_register_invalid_email(self) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/auth/register",
                    json={
                        "email": "not-an-email",
                        "password": "strongpassword",
                    },
                )
                assert resp.status_code == 422

        asyncio.run(_run())

    @patch("shomer.routes.auth.send_email_task")
    def test_register_with_username(self, mock_task: MagicMock) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/auth/register",
                    json={
                        "email": "user@example.com",
                        "password": "strongpassword",
                        "username": "johndoe",
                    },
                )
                assert resp.status_code == 201

        asyncio.run(_run())

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Integration tests for POST /auth/verify and /auth/verify/resend."""

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
from shomer.models.user_email import UserEmail  # noqa: F401
from shomer.models.user_password import UserPassword  # noqa: F401
from shomer.models.user_profile import UserProfile  # noqa: F401
from shomer.models.verification_code import VerificationCode

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


class TestVerifyEndpoint:
    """Integration tests for POST /auth/verify."""

    @patch("shomer.routes.auth.send_email_task")
    def test_verify_success(self, mock_task: MagicMock) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                # Register first
                await client.post(
                    "/auth/register",
                    json={"email": "v@example.com", "password": "securepassword"},
                )

                # Get code from DB
                async with _SESSION_FACTORY() as session:
                    result = await session.execute(
                        select(VerificationCode).where(
                            VerificationCode.email == "v@example.com"
                        )
                    )
                    vc = result.scalar_one()
                    code = vc.code

                resp = await client.post(
                    "/auth/verify",
                    json={"email": "v@example.com", "code": code},
                )
                assert resp.status_code == 200
                assert "verified" in resp.json()["message"].lower()

        asyncio.run(_run())

    def test_verify_invalid_code(self) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/auth/verify",
                    json={"email": "nobody@example.com", "code": "000000"},
                )
                assert resp.status_code == 400

        asyncio.run(_run())

    def test_verify_short_code_422(self) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/auth/verify",
                    json={"email": "t@example.com", "code": "12"},
                )
                assert resp.status_code == 422

        asyncio.run(_run())


class TestResendEndpoint:
    """Integration tests for POST /auth/verify/resend."""

    def test_resend_unknown_email(self) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/auth/verify/resend",
                    json={"email": "unknown@example.com"},
                )
                assert resp.status_code == 404

        asyncio.run(_run())

    @patch("shomer.routes.auth.send_email_task")
    def test_resend_rate_limit(self, mock_task: MagicMock) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                # Register (creates a code)
                await client.post(
                    "/auth/register",
                    json={"email": "rl@example.com", "password": "securepassword"},
                )
                # Resend immediately should be rate limited
                resp = await client.post(
                    "/auth/verify/resend",
                    json={"email": "rl@example.com"},
                )
                assert resp.status_code == 429

        asyncio.run(_run())

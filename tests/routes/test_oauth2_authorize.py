# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Integration tests for GET /oauth2/authorize."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterator
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from shomer.app import app
from shomer.core.database import Base
from shomer.deps import get_db
from shomer.models.access_token import AccessToken  # noqa: F401
from shomer.models.authorization_code import AuthorizationCode  # noqa: F401
from shomer.models.jwk import JWK  # noqa: F401
from shomer.models.oauth2_client import OAuth2Client  # noqa: F401
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


class TestAuthorizeEndpoint:
    """Integration tests for GET /oauth2/authorize."""

    def test_missing_client_id_returns_400(self) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.get(
                    "/oauth2/authorize",
                    params={"response_type": "code", "state": "abc"},
                    follow_redirects=False,
                )
                assert resp.status_code == 400

        asyncio.run(_run())

    def test_unknown_client_returns_400_not_redirect(self) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.get(
                    "/oauth2/authorize",
                    params={
                        "client_id": "nonexistent",
                        "redirect_uri": "https://app.example.com/cb",
                        "response_type": "code",
                        "state": "abc",
                    },
                    follow_redirects=False,
                )
                # OWASP: never redirect to unvalidated redirect_uri
                assert resp.status_code == 400

        asyncio.run(_run())

    def test_unauthenticated_redirects_to_login(self) -> None:
        async def _run() -> None:
            # Create a client first
            from shomer.services.oauth2_client_service import OAuth2ClientService

            async with _SESSION_FACTORY() as db:
                svc = OAuth2ClientService(db)
                client, _ = await svc.create_client(
                    client_name="App",
                    redirect_uris=["https://app.example.com/cb"],
                    response_types=["code"],
                    grant_types=["authorization_code"],
                    scopes=["openid"],
                )
                await db.commit()
                cid = client.client_id

            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as http_client:
                resp = await http_client.get(
                    "/oauth2/authorize",
                    params={
                        "client_id": cid,
                        "redirect_uri": "https://app.example.com/cb",
                        "response_type": "code",
                        "scope": "openid",
                        "state": "abc123",
                    },
                    follow_redirects=False,
                )
                assert resp.status_code == 302
                assert "/ui/login" in resp.headers["location"]

        asyncio.run(_run())

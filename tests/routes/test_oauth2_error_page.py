# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for OAuth2 error page rendering."""

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
from shomer.routes.oauth2 import _FRIENDLY_ERROR_MESSAGES

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


class TestOAuth2ErrorPage:
    """Tests for OAuth2 error page rendering."""

    def test_missing_client_id_returns_html_400(self) -> None:
        """Missing client_id renders an HTML error page with 400."""

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
                assert "text/html" in resp.headers.get("content-type", "")
                assert "Authorization Error" in resp.text
                assert "client_id" in resp.text

        asyncio.run(_run())

    def test_unknown_client_shows_friendly_message(self) -> None:
        """Unknown client_id shows the 'missing parameters' friendly message."""

        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.get(
                    "/oauth2/authorize",
                    params={
                        "client_id": "nonexistent",
                        "redirect_uri": "https://evil.com",
                        "response_type": "code",
                        "state": "abc",
                    },
                    follow_redirects=False,
                )
                assert resp.status_code == 400
                assert "Unknown client_id" in resp.text
                assert "invalid_request" in resp.text

        asyncio.run(_run())

    def test_error_page_contains_back_link(self) -> None:
        """Error page includes a link back to home."""

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
                assert "Back to Home" in resp.text
                assert 'href="/"' in resp.text

        asyncio.run(_run())


class TestFriendlyMessages:
    """Tests for _FRIENDLY_ERROR_MESSAGES mapping."""

    def test_known_errors_have_messages(self) -> None:
        assert "invalid_client" in _FRIENDLY_ERROR_MESSAGES
        assert "invalid_request" in _FRIENDLY_ERROR_MESSAGES
        assert "unauthorized_client" in _FRIENDLY_ERROR_MESSAGES
        assert "access_denied" in _FRIENDLY_ERROR_MESSAGES
        assert "server_error" in _FRIENDLY_ERROR_MESSAGES

    def test_messages_are_non_empty(self) -> None:
        for code, msg in _FRIENDLY_ERROR_MESSAGES.items():
            assert len(msg) > 0, f"Empty message for {code}"

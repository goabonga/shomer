# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for GET /api/me profile endpoint."""

from __future__ import annotations

import asyncio
import json
import uuid
from unittest.mock import AsyncMock, MagicMock

from shomer.auth import CurrentUserInfo
from shomer.routes.profile import _build_profile, get_me


def _user(scopes: list[str] | None = None) -> CurrentUserInfo:
    return CurrentUserInfo(
        user_id=uuid.uuid4(),
        scopes=scopes or ["openid"],
        auth_method="bearer",
    )


def _mock_db(
    db_user: MagicMock | None = None,
    session_count: int = 0,
) -> AsyncMock:
    db = AsyncMock()
    # First call: user lookup, second call: session count
    user_result = MagicMock()
    user_result.scalar_one_or_none.return_value = db_user
    count_result = MagicMock()
    count_result.scalar.return_value = session_count
    db.execute.side_effect = [user_result, count_result]
    return db


def _mock_user(
    *,
    username: str = "johndoe",
    with_profile: bool = True,
    email: str = "john@example.com",
) -> MagicMock:
    u = MagicMock()
    u.username = username
    u.is_active = True

    e = MagicMock()
    e.email = email
    e.is_primary = True
    e.is_verified = True
    u.emails = [e]

    if with_profile:
        p = MagicMock()
        p.name = "John Doe"
        p.given_name = "John"
        p.family_name = "Doe"
        p.nickname = None
        p.preferred_username = "johndoe"
        p.gender = None
        p.birthdate = None
        p.zoneinfo = "Europe/Paris"
        p.locale = "fr-FR"
        p.picture_url = "https://example.com/pic.jpg"
        p.profile_url = None
        u.profile = p
    else:
        u.profile = None

    return u


class TestBuildProfile:
    """Tests for _build_profile()."""

    def test_user_id_and_auth_method(self) -> None:
        async def _run() -> None:
            user = _user()
            profile = await _build_profile(user, _mock_db())
            assert profile["user_id"] == str(user.user_id)
            assert profile["auth_method"] == "bearer"

        asyncio.run(_run())

    def test_user_not_found(self) -> None:
        async def _run() -> None:
            user = _user()
            db = AsyncMock()
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db.execute.return_value = result
            profile = await _build_profile(user, db)
            assert "username" not in profile

        asyncio.run(_run())

    def test_includes_emails(self) -> None:
        async def _run() -> None:
            user = _user()
            db_user = _mock_user(email="j@example.com")
            profile = await _build_profile(user, _mock_db(db_user))
            assert len(profile["emails"]) == 1
            assert profile["emails"][0]["email"] == "j@example.com"
            assert profile["emails"][0]["is_verified"] is True

        asyncio.run(_run())

    def test_includes_profile_data(self) -> None:
        async def _run() -> None:
            user = _user()
            db_user = _mock_user()
            profile = await _build_profile(user, _mock_db(db_user))
            assert profile["profile"]["name"] == "John Doe"
            assert profile["profile"]["picture"] == "https://example.com/pic.jpg"
            assert profile["profile"]["zoneinfo"] == "Europe/Paris"
            assert "nickname" not in profile["profile"]

        asyncio.run(_run())

    def test_no_profile_returns_null(self) -> None:
        async def _run() -> None:
            user = _user()
            db_user = _mock_user(with_profile=False)
            profile = await _build_profile(user, _mock_db(db_user))
            assert profile["profile"] is None

        asyncio.run(_run())

    def test_session_count(self) -> None:
        async def _run() -> None:
            user = _user()
            db_user = _mock_user()
            profile = await _build_profile(user, _mock_db(db_user, session_count=3))
            assert profile["active_sessions"] == 3

        asyncio.run(_run())

    def test_tenants_placeholder(self) -> None:
        async def _run() -> None:
            user = _user()
            db_user = _mock_user()
            profile = await _build_profile(user, _mock_db(db_user))
            assert profile["tenants"] == []

        asyncio.run(_run())

    def test_includes_scopes(self) -> None:
        async def _run() -> None:
            user = _user(scopes=["openid", "profile"])
            profile = await _build_profile(user, _mock_db())
            assert profile["scopes"] == ["openid", "profile"]

        asyncio.run(_run())


class TestGetMe:
    """Tests for GET /api/me."""

    def test_returns_json(self) -> None:
        async def _run() -> None:
            user = _user()
            resp = await get_me(user, _mock_db())
            body = json.loads(bytes(resp.body))
            assert "user_id" in body

        asyncio.run(_run())

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for OIDC UserInfo endpoint."""

from __future__ import annotations

import asyncio
import json
import uuid
from unittest.mock import AsyncMock, MagicMock

from shomer.auth import CurrentUserInfo
from shomer.routes.userinfo import _build_userinfo, userinfo_get, userinfo_post


def _user(
    scopes: list[str] | None = None,
) -> CurrentUserInfo:
    return CurrentUserInfo(
        user_id=uuid.uuid4(),
        scopes=scopes or [],
        auth_method="bearer",
    )


def _mock_db(
    db_user: MagicMock | None = None,
) -> AsyncMock:
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = db_user
    db.execute.return_value = result
    return db


def _mock_user_with_profile(
    *,
    email: str = "user@example.com",
    email_verified: bool = True,
    name: str | None = "John Doe",
    phone: str | None = None,
) -> MagicMock:
    u = MagicMock()
    u.id = uuid.uuid4()

    primary_email = MagicMock()
    primary_email.email = email
    primary_email.is_primary = True
    primary_email.is_verified = email_verified
    u.emails = [primary_email]

    profile = MagicMock()
    profile.name = name
    profile.given_name = "John"
    profile.family_name = "Doe"
    profile.middle_name = None
    profile.nickname = None
    profile.preferred_username = None
    profile.profile_url = None
    profile.picture_url = "https://example.com/pic.jpg"
    profile.website = None
    profile.gender = None
    profile.birthdate = None
    profile.zoneinfo = None
    profile.locale = None
    profile.address_formatted = None
    profile.address_street = None
    profile.address_locality = None
    profile.address_region = None
    profile.address_postal_code = None
    profile.address_country = None
    profile.phone_number = phone
    profile.phone_number_verified = False
    u.profile = profile

    return u


class TestBuildUserinfo:
    """Tests for _build_userinfo()."""

    def test_sub_always_included(self) -> None:
        async def _run() -> None:
            user = _user()
            claims = await _build_userinfo(user, _mock_db())
            assert claims["sub"] == str(user.user_id)

        asyncio.run(_run())

    def test_no_claims_without_scopes(self) -> None:
        async def _run() -> None:
            user = _user(scopes=[])
            db_user = _mock_user_with_profile()
            claims = await _build_userinfo(user, _mock_db(db_user))
            assert list(claims.keys()) == ["sub"]

        asyncio.run(_run())

    def test_email_scope(self) -> None:
        async def _run() -> None:
            user = _user(scopes=["openid", "email"])
            db_user = _mock_user_with_profile(email="j@example.com")
            claims = await _build_userinfo(user, _mock_db(db_user))
            assert claims["email"] == "j@example.com"
            assert claims["email_verified"] is True

        asyncio.run(_run())

    def test_profile_scope(self) -> None:
        async def _run() -> None:
            user = _user(scopes=["openid", "profile"])
            db_user = _mock_user_with_profile(name="Jane")
            claims = await _build_userinfo(user, _mock_db(db_user))
            assert claims["name"] == "Jane"
            assert claims["given_name"] == "John"
            assert claims["picture"] == "https://example.com/pic.jpg"
            assert "middle_name" not in claims

        asyncio.run(_run())

    def test_phone_scope(self) -> None:
        async def _run() -> None:
            user = _user(scopes=["openid", "phone"])
            db_user = _mock_user_with_profile(phone="+33612345678")
            claims = await _build_userinfo(user, _mock_db(db_user))
            assert claims["phone_number"] == "+33612345678"
            assert claims["phone_number_verified"] is False

        asyncio.run(_run())

    def test_address_scope(self) -> None:
        async def _run() -> None:
            user = _user(scopes=["openid", "address"])
            db_user = _mock_user_with_profile()
            db_user.profile.address_formatted = "123 Main St"
            db_user.profile.address_country = "France"
            claims = await _build_userinfo(user, _mock_db(db_user))
            assert claims["address"]["formatted"] == "123 Main St"
            assert claims["address"]["country"] == "France"

        asyncio.run(_run())

    def test_user_not_found(self) -> None:
        async def _run() -> None:
            user = _user(scopes=["openid", "profile"])
            claims = await _build_userinfo(user, _mock_db(None))
            assert claims == {"sub": str(user.user_id)}

        asyncio.run(_run())

    def test_no_profile_object(self) -> None:
        async def _run() -> None:
            user = _user(scopes=["openid", "profile"])
            db_user = MagicMock()
            db_user.emails = []
            db_user.profile = None
            claims = await _build_userinfo(user, _mock_db(db_user))
            assert "name" not in claims

        asyncio.run(_run())


class TestUserinfoGet:
    """Tests for GET /userinfo."""

    def test_returns_json_response(self) -> None:
        async def _run() -> None:
            user = _user(scopes=["openid"])
            resp = await userinfo_get(user, _mock_db())
            body = json.loads(bytes(resp.body))
            assert "sub" in body

        asyncio.run(_run())


class TestUserinfoPost:
    """Tests for POST /userinfo."""

    def test_returns_json_response(self) -> None:
        async def _run() -> None:
            user = _user(scopes=["openid"])
            resp = await userinfo_post(user, _mock_db())
            body = json.loads(bytes(resp.body))
            assert "sub" in body

        asyncio.run(_run())

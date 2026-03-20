# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for /api/me profile and email management endpoints."""

from __future__ import annotations

import asyncio
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

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


class TestUpdateProfile:
    """Tests for PUT /api/me/profile."""

    def test_creates_profile_if_missing(self) -> None:
        async def _run() -> None:
            from shomer.routes.profile import ProfileUpdateRequest, update_profile

            user = _user()
            db = AsyncMock()
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db.execute.return_value = result
            db.add = MagicMock()
            db.flush = AsyncMock()

            body = ProfileUpdateRequest(name="Jane Doe")
            resp = await update_profile(body, user, db)
            body_json = json.loads(bytes(resp.body))
            assert body_json["message"] == "Profile updated"
            db.add.assert_called_once()

        asyncio.run(_run())

    def test_updates_existing_profile(self) -> None:
        async def _run() -> None:
            from shomer.routes.profile import ProfileUpdateRequest, update_profile

            user = _user()
            db = AsyncMock()
            mock_profile = MagicMock()
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_profile
            db.execute.return_value = result
            db.flush = AsyncMock()

            body = ProfileUpdateRequest(name="Updated", locale="en-US")
            await update_profile(body, user, db)
            assert mock_profile.name == "Updated"
            assert mock_profile.locale == "en-US"

        asyncio.run(_run())

    def test_only_updates_provided_fields(self) -> None:
        async def _run() -> None:
            from shomer.routes.profile import ProfileUpdateRequest, update_profile

            user = _user()
            db = AsyncMock()
            mock_profile = MagicMock()
            mock_profile.name = "Original"
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_profile
            db.execute.return_value = result
            db.flush = AsyncMock()

            body = ProfileUpdateRequest(locale="fr-FR")
            await update_profile(body, user, db)
            assert mock_profile.locale == "fr-FR"
            # name should not be changed (not in update_data)

        asyncio.run(_run())


class TestAddEmail:
    """Tests for POST /api/me/emails."""

    @patch("shomer.tasks.email.send_email_task")
    def test_add_email_success(self, mock_task: MagicMock) -> None:
        async def _run() -> None:
            from shomer.routes.profile import AddEmailRequest, add_email

            user = _user()
            db = AsyncMock()
            # email not existing
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db.execute.return_value = result
            db.add = MagicMock()
            db.flush = AsyncMock()

            body = AddEmailRequest(email="new@example.com")
            resp = await add_email(body, user, db)
            assert resp.status_code == 201
            mock_task.delay.assert_called_once()

        asyncio.run(_run())

    def test_add_duplicate_email_409(self) -> None:
        async def _run() -> None:
            from shomer.routes.profile import AddEmailRequest, add_email

            user = _user()
            db = AsyncMock()
            result = MagicMock()
            result.scalar_one_or_none.return_value = MagicMock()  # exists
            db.execute.return_value = result

            body = AddEmailRequest(email="dupe@example.com")
            with pytest.raises(HTTPException) as exc_info:
                await add_email(body, user, db)
            assert exc_info.value.status_code == 409

        asyncio.run(_run())


class TestDeleteEmail:
    """Tests for DELETE /api/me/emails/{id}."""

    def test_delete_success(self) -> None:
        async def _run() -> None:
            from shomer.routes.profile import delete_email

            user = _user()
            db = AsyncMock()
            mock_email = MagicMock()
            mock_email.is_primary = False
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_email
            db.execute.return_value = result
            db.delete = AsyncMock()
            db.flush = AsyncMock()

            resp = await delete_email(str(uuid.uuid4()), user, db)
            body = json.loads(bytes(resp.body))
            assert body["message"] == "Email removed"

        asyncio.run(_run())

    def test_delete_primary_400(self) -> None:
        async def _run() -> None:
            from shomer.routes.profile import delete_email

            user = _user()
            db = AsyncMock()
            mock_email = MagicMock()
            mock_email.is_primary = True
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_email
            db.execute.return_value = result

            with pytest.raises(HTTPException) as exc_info:
                await delete_email(str(uuid.uuid4()), user, db)
            assert exc_info.value.status_code == 400

        asyncio.run(_run())

    def test_delete_not_found_404(self) -> None:
        async def _run() -> None:
            from shomer.routes.profile import delete_email

            user = _user()
            db = AsyncMock()
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db.execute.return_value = result

            with pytest.raises(HTTPException) as exc_info:
                await delete_email(str(uuid.uuid4()), user, db)
            assert exc_info.value.status_code == 404

        asyncio.run(_run())

    def test_delete_invalid_id_400(self) -> None:
        async def _run() -> None:
            from shomer.routes.profile import delete_email

            with pytest.raises(HTTPException) as exc_info:
                await delete_email("not-a-uuid", _user(), AsyncMock())
            assert exc_info.value.status_code == 400

        asyncio.run(_run())


class TestSetPrimaryEmail:
    """Tests for PUT /api/me/emails/{id}/primary."""

    def test_set_primary_success(self) -> None:
        async def _run() -> None:
            from shomer.routes.profile import set_primary_email

            user = _user()
            eid = uuid.uuid4()
            db = AsyncMock()

            target = MagicMock()
            target.id = eid
            target.is_verified = True
            target_result = MagicMock()
            target_result.scalar_one_or_none.return_value = target

            other = MagicMock()
            other.id = uuid.uuid4()
            all_result = MagicMock()
            all_result.scalars.return_value.all.return_value = [target, other]

            db.execute.side_effect = [target_result, all_result]
            db.flush = AsyncMock()

            resp = await set_primary_email(str(eid), user, db)
            body = json.loads(bytes(resp.body))
            assert body["message"] == "Primary email updated"
            assert target.is_primary is True
            assert other.is_primary is False

        asyncio.run(_run())

    def test_set_unverified_400(self) -> None:
        async def _run() -> None:
            from shomer.routes.profile import set_primary_email

            user = _user()
            db = AsyncMock()
            target = MagicMock()
            target.is_verified = False
            result = MagicMock()
            result.scalar_one_or_none.return_value = target
            db.execute.return_value = result

            with pytest.raises(HTTPException) as exc_info:
                await set_primary_email(str(uuid.uuid4()), user, db)
            assert exc_info.value.status_code == 400
            assert "unverified" in str(exc_info.value.detail).lower()

        asyncio.run(_run())

    def test_set_not_found_404(self) -> None:
        async def _run() -> None:
            from shomer.routes.profile import set_primary_email

            user = _user()
            db = AsyncMock()
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db.execute.return_value = result

            with pytest.raises(HTTPException) as exc_info:
                await set_primary_email(str(uuid.uuid4()), user, db)
            assert exc_info.value.status_code == 404

        asyncio.run(_run())

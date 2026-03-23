# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for admin users API routes."""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from shomer.routes.admin_users import create_user, get_user, list_users


def _mock_user(
    username: str = "alice",
    email: str = "alice@example.com",
    is_active: bool = True,
) -> MagicMock:
    """Create a mock User with emails."""
    u = MagicMock()
    u.id = uuid.uuid4()
    u.username = username
    u.is_active = is_active
    u.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    e = MagicMock()
    e.id = uuid.uuid4()
    e.email = email
    e.is_primary = True
    e.is_verified = True
    u.emails = [e]
    return u


class TestListUsers:
    """Tests for GET /admin/users."""

    @patch("shomer.routes.admin_users.require_scope")
    def test_returns_paginated_users(self, _mock_rbac: MagicMock) -> None:
        """Returns a paginated list of users."""

        async def _run() -> None:
            mock_user = _mock_user()

            # Mock for count query
            count_result = MagicMock()
            count_result.scalar.return_value = 1

            # Mock for user list query
            scalars_mock = MagicMock()
            scalars_mock.unique.return_value = scalars_mock
            scalars_mock.all.return_value = [mock_user]
            list_result = MagicMock()
            list_result.scalars.return_value = scalars_mock

            db = AsyncMock()
            db.execute.side_effect = [count_result, list_result]

            resp = await list_users(db, q=None, is_active=None, page=1, page_size=20)
            data = json.loads(bytes(resp.body))
            assert data["total"] == 1
            assert data["page"] == 1
            assert data["page_size"] == 20
            assert len(data["items"]) == 1
            assert data["items"][0]["username"] == "alice"
            assert data["items"][0]["email"] == "alice@example.com"
            assert data["items"][0]["is_active"] is True

        asyncio.run(_run())

    @patch("shomer.routes.admin_users.require_scope")
    def test_returns_empty_when_no_users(self, _mock_rbac: MagicMock) -> None:
        """Returns empty list when no users match."""

        async def _run() -> None:
            count_result = MagicMock()
            count_result.scalar.return_value = 0

            scalars_mock = MagicMock()
            scalars_mock.unique.return_value = scalars_mock
            scalars_mock.all.return_value = []
            list_result = MagicMock()
            list_result.scalars.return_value = scalars_mock

            db = AsyncMock()
            db.execute.side_effect = [count_result, list_result]

            resp = await list_users(db, q=None, is_active=None, page=1, page_size=20)
            data = json.loads(bytes(resp.body))
            assert data["total"] == 0
            assert data["items"] == []

        asyncio.run(_run())

    @patch("shomer.routes.admin_users.require_scope")
    def test_pagination_params(self, _mock_rbac: MagicMock) -> None:
        """Respects page and page_size parameters."""

        async def _run() -> None:
            count_result = MagicMock()
            count_result.scalar.return_value = 50

            scalars_mock = MagicMock()
            scalars_mock.unique.return_value = scalars_mock
            scalars_mock.all.return_value = []
            list_result = MagicMock()
            list_result.scalars.return_value = scalars_mock

            db = AsyncMock()
            db.execute.side_effect = [count_result, list_result]

            resp = await list_users(db, q=None, is_active=None, page=3, page_size=10)
            data = json.loads(bytes(resp.body))
            assert data["page"] == 3
            assert data["page_size"] == 10
            assert data["total"] == 50

        asyncio.run(_run())

    @patch("shomer.routes.admin_users.require_scope")
    def test_user_without_email(self, _mock_rbac: MagicMock) -> None:
        """Handles users with no emails gracefully."""

        async def _run() -> None:
            mock_user = _mock_user()
            mock_user.emails = []

            count_result = MagicMock()
            count_result.scalar.return_value = 1

            scalars_mock = MagicMock()
            scalars_mock.unique.return_value = scalars_mock
            scalars_mock.all.return_value = [mock_user]
            list_result = MagicMock()
            list_result.scalars.return_value = scalars_mock

            db = AsyncMock()
            db.execute.side_effect = [count_result, list_result]

            resp = await list_users(db, q=None, is_active=None, page=1, page_size=20)
            data = json.loads(bytes(resp.body))
            assert data["items"][0]["email"] is None

        asyncio.run(_run())


class TestGetUser:
    """Tests for GET /admin/users/{id}."""

    @patch("shomer.routes.admin_users.require_scope")
    def test_returns_detailed_user(self, _mock_rbac: MagicMock) -> None:
        """Returns full user detail with emails, roles, sessions, memberships."""

        async def _run() -> None:
            user_id = uuid.uuid4()
            mock_user = _mock_user()
            mock_user.id = user_id
            profile = MagicMock()
            profile.name = "Alice"
            profile.given_name = "Alice"
            profile.family_name = None
            profile.nickname = None
            profile.preferred_username = None
            profile.gender = None
            profile.locale = "en-US"
            profile.zoneinfo = None
            mock_user.profile = profile

            # user query result
            user_result = MagicMock()
            user_result.scalar_one_or_none.return_value = mock_user

            # roles query result
            mock_role = MagicMock()
            mock_role.id = uuid.uuid4()
            mock_role.name = "admin"
            mock_ur = MagicMock()
            mock_ur.role = mock_role
            mock_ur.tenant_id = None
            mock_ur.expires_at = None
            roles_scalars = MagicMock()
            roles_scalars.all.return_value = [mock_ur]
            roles_result = MagicMock()
            roles_result.scalars.return_value = roles_scalars

            # session count result
            session_result = MagicMock()
            session_result.scalar.return_value = 2

            # memberships result
            memberships_scalars = MagicMock()
            memberships_scalars.all.return_value = []
            memberships_result = MagicMock()
            memberships_result.scalars.return_value = memberships_scalars

            db = AsyncMock()
            db.execute.side_effect = [
                user_result,
                roles_result,
                session_result,
                memberships_result,
            ]

            resp = await get_user(str(user_id), db)
            data = json.loads(bytes(resp.body))
            assert data["id"] == str(user_id)
            assert data["username"] == "alice"
            assert data["is_active"] is True
            assert len(data["emails"]) == 1
            assert data["profile"]["name"] == "Alice"
            assert data["profile"]["locale"] == "en-US"
            assert len(data["roles"]) == 1
            assert data["roles"][0]["name"] == "admin"
            assert data["active_sessions"] == 2
            assert data["memberships"] == []

        asyncio.run(_run())

    @patch("shomer.routes.admin_users.require_scope")
    def test_invalid_uuid_returns_400(self, _mock_rbac: MagicMock) -> None:
        """Returns 400 for invalid UUID."""

        async def _run() -> None:
            try:
                await get_user("not-a-uuid", AsyncMock())
                raise AssertionError("Expected HTTPException")
            except HTTPException as exc:
                assert exc.status_code == 400

        asyncio.run(_run())

    @patch("shomer.routes.admin_users.require_scope")
    def test_not_found_returns_404(self, _mock_rbac: MagicMock) -> None:
        """Returns 404 when user does not exist."""

        async def _run() -> None:
            from fastapi import HTTPException

            user_result = MagicMock()
            user_result.scalar_one_or_none.return_value = None

            db = AsyncMock()
            db.execute.return_value = user_result

            try:
                await get_user(str(uuid.uuid4()), db)
                raise AssertionError("Expected HTTPException")
            except HTTPException as exc:
                assert exc.status_code == 404

        asyncio.run(_run())


class TestCreateUser:
    """Tests for POST /admin/users."""

    @patch("shomer.routes.admin_users.require_scope")
    @patch("shomer.core.security.hash_password", return_value="hashed")
    @patch("shomer.models.queries.create_user")
    def test_creates_user_successfully(
        self,
        mock_create: AsyncMock,
        _mock_hash: MagicMock,
        _mock_rbac: MagicMock,
    ) -> None:
        """Creates a user and returns 201."""

        async def _run() -> None:
            new_user = _mock_user(email="new@example.com")
            mock_create.return_value = new_user

            # email check returns None (not existing)
            email_result = MagicMock()
            email_result.scalar_one_or_none.return_value = None

            # _get_user_emails returns a mock email record
            email_record = MagicMock()
            email_record.is_verified = False
            emails_scalars = MagicMock()
            emails_scalars.all.return_value = [email_record]
            emails_result = MagicMock()
            emails_result.scalars.return_value = emails_scalars

            db = AsyncMock()
            db.execute.side_effect = [email_result, emails_result]

            from shomer.routes.admin_users import AdminCreateUserRequest

            body = AdminCreateUserRequest(
                email="new@example.com", password="password123"
            )
            resp = await create_user(body, db)
            assert resp.status_code == 201
            data = json.loads(bytes(resp.body))
            assert data["email"] == "new@example.com"
            assert data["email_verified"] is True

        asyncio.run(_run())

    @patch("shomer.routes.admin_users.require_scope")
    def test_duplicate_email_returns_409(self, _mock_rbac: MagicMock) -> None:
        """Returns 409 when email already exists."""

        async def _run() -> None:
            email_result = MagicMock()
            email_result.scalar_one_or_none.return_value = MagicMock()

            db = AsyncMock()
            db.execute.return_value = email_result

            from shomer.routes.admin_users import AdminCreateUserRequest

            body = AdminCreateUserRequest(
                email="dup@example.com", password="password123"
            )
            try:
                await create_user(body, db)
                raise AssertionError("Expected HTTPException")
            except HTTPException as exc:
                assert exc.status_code == 409

        asyncio.run(_run())

        asyncio.run(_run())

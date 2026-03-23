# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for admin users API routes."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from shomer.routes.admin_users import list_users


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
    e.email = email
    e.is_primary = True
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
            import json

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
            import json

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
            import json

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
            import json

            data = json.loads(bytes(resp.body))
            assert data["items"][0]["email"] is None

        asyncio.run(_run())

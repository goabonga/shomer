# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for admin sessions API routes."""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from shomer.routes.admin_sessions import (
    get_session,
    list_sessions,
    revoke_session,
    revoke_user_sessions,
)


def _mock_session() -> MagicMock:
    """Create a mock Session."""
    s = MagicMock()
    s.id = uuid.uuid4()
    s.user_id = uuid.uuid4()
    s.tenant_id = None
    s.ip_address = "192.168.1.1"
    s.user_agent = "Mozilla/5.0"
    now = datetime.now(timezone.utc)
    s.last_activity = now
    s.expires_at = now + timedelta(hours=1)
    s.created_at = now - timedelta(hours=2)
    return s


class TestListSessions:
    """Tests for GET /admin/sessions."""

    @patch("shomer.routes.admin_sessions.require_scope")
    def test_returns_paginated_sessions(self, _mock_rbac: MagicMock) -> None:
        """Returns a paginated list of sessions."""

        async def _run() -> None:
            mock_sess = _mock_session()

            count_result = MagicMock()
            count_result.scalar.return_value = 1

            scalars_mock = MagicMock()
            scalars_mock.all.return_value = [mock_sess]
            list_result = MagicMock()
            list_result.scalars.return_value = scalars_mock

            db = AsyncMock()
            db.execute.side_effect = [count_result, list_result]

            resp = await list_sessions(
                db,
                user_id=None,
                tenant_id=None,
                active_only=True,
                page=1,
                page_size=20,
            )
            data = json.loads(bytes(resp.body))
            assert data["total"] == 1
            assert len(data["items"]) == 1
            assert data["items"][0]["user_id"] == str(mock_sess.user_id)
            assert data["items"][0]["ip_address"] == "192.168.1.1"

        asyncio.run(_run())

    @patch("shomer.routes.admin_sessions.require_scope")
    def test_empty_list(self, _mock_rbac: MagicMock) -> None:
        """Returns empty list when no sessions match."""

        async def _run() -> None:
            count_result = MagicMock()
            count_result.scalar.return_value = 0
            scalars_mock = MagicMock()
            scalars_mock.all.return_value = []
            list_result = MagicMock()
            list_result.scalars.return_value = scalars_mock

            db = AsyncMock()
            db.execute.side_effect = [count_result, list_result]

            resp = await list_sessions(
                db,
                user_id=None,
                tenant_id=None,
                active_only=False,
                page=1,
                page_size=20,
            )
            data = json.loads(bytes(resp.body))
            assert data["total"] == 0
            assert data["items"] == []

        asyncio.run(_run())

    @patch("shomer.routes.admin_sessions.require_scope")
    def test_invalid_user_id_returns_400(self, _mock_rbac: MagicMock) -> None:
        """Returns 400 for invalid user_id filter."""

        async def _run() -> None:
            try:
                await list_sessions(
                    AsyncMock(),
                    user_id="bad",
                    tenant_id=None,
                    active_only=True,
                    page=1,
                    page_size=20,
                )
                raise AssertionError("Expected HTTPException")
            except HTTPException as exc:
                assert exc.status_code == 400

        asyncio.run(_run())


class TestGetSession:
    """Tests for GET /admin/sessions/{id}."""

    @patch("shomer.routes.admin_sessions.require_scope")
    def test_returns_session_detail(self, _mock_rbac: MagicMock) -> None:
        """Returns full session details."""

        async def _run() -> None:
            mock_sess = _mock_session()
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_sess

            db = AsyncMock()
            db.execute.return_value = result

            resp = await get_session(str(mock_sess.id), db)
            data = json.loads(bytes(resp.body))
            assert data["id"] == str(mock_sess.id)
            assert data["ip_address"] == "192.168.1.1"
            assert data["user_agent"] == "Mozilla/5.0"

        asyncio.run(_run())

    @patch("shomer.routes.admin_sessions.require_scope")
    def test_invalid_uuid_returns_400(self, _mock_rbac: MagicMock) -> None:
        """Returns 400 for invalid UUID."""

        async def _run() -> None:
            try:
                await get_session("bad", AsyncMock())
                raise AssertionError("Expected HTTPException")
            except HTTPException as exc:
                assert exc.status_code == 400

        asyncio.run(_run())

    @patch("shomer.routes.admin_sessions.require_scope")
    def test_not_found_returns_404(self, _mock_rbac: MagicMock) -> None:
        """Returns 404 when not found."""

        async def _run() -> None:
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db = AsyncMock()
            db.execute.return_value = result

            try:
                await get_session(str(uuid.uuid4()), db)
                raise AssertionError("Expected HTTPException")
            except HTTPException as exc:
                assert exc.status_code == 404

        asyncio.run(_run())


class TestRevokeSession:
    """Tests for DELETE /admin/sessions/{id}."""

    @patch("shomer.routes.admin_sessions.require_scope")
    def test_revokes_session(self, _mock_rbac: MagicMock) -> None:
        """Deletes the session and returns confirmation."""

        async def _run() -> None:
            mock_sess = _mock_session()
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_sess

            db = AsyncMock()
            db.execute.return_value = result

            resp = await revoke_session(str(mock_sess.id), db)
            data = json.loads(bytes(resp.body))
            assert data["message"] == "Session revoked successfully"
            db.delete.assert_awaited_once_with(mock_sess)

        asyncio.run(_run())

    @patch("shomer.routes.admin_sessions.require_scope")
    def test_not_found_returns_404(self, _mock_rbac: MagicMock) -> None:
        """Returns 404 when not found."""

        async def _run() -> None:
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db = AsyncMock()
            db.execute.return_value = result

            try:
                await revoke_session(str(uuid.uuid4()), db)
                raise AssertionError("Expected HTTPException")
            except HTTPException as exc:
                assert exc.status_code == 404

        asyncio.run(_run())


class TestRevokeUserSessions:
    """Tests for DELETE /admin/sessions/users/{user_id}."""

    @patch("shomer.routes.admin_sessions.require_scope")
    def test_revokes_all_user_sessions(self, _mock_rbac: MagicMock) -> None:
        """Deletes all sessions for a user."""

        async def _run() -> None:
            uid = uuid.uuid4()
            sid1, sid2 = uuid.uuid4(), uuid.uuid4()

            scalars_mock = MagicMock()
            scalars_mock.all.return_value = [sid1, sid2]
            result = MagicMock()
            result.scalars.return_value = scalars_mock

            db = AsyncMock()
            db.execute.return_value = result

            resp = await revoke_user_sessions(str(uid), db)
            data = json.loads(bytes(resp.body))
            assert data["revoked_count"] == 2
            assert data["message"] == "All user sessions revoked"

        asyncio.run(_run())

    @patch("shomer.routes.admin_sessions.require_scope")
    def test_invalid_user_id_returns_400(self, _mock_rbac: MagicMock) -> None:
        """Returns 400 for invalid user UUID."""

        async def _run() -> None:
            try:
                await revoke_user_sessions("bad", AsyncMock())
                raise AssertionError("Expected HTTPException")
            except HTTPException as exc:
                assert exc.status_code == 400

        asyncio.run(_run())

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for admin PATs API routes."""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from shomer.routes.admin_pats import get_pat, list_pats, revoke_pat


def _mock_pat(name: str = "CI Key") -> MagicMock:
    """Create a mock PersonalAccessToken."""
    p = MagicMock()
    p.id = uuid.uuid4()
    p.user_id = uuid.uuid4()
    p.name = name
    p.token_prefix = "shm_pat_abc"
    p.scopes = "admin:users:read"
    p.is_revoked = False
    p.expires_at = None
    p.last_used_at = None
    p.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return p


class TestListPATs:
    """Tests for GET /admin/pats."""

    @patch("shomer.routes.admin_pats.require_scope")
    def test_returns_paginated_pats(self, _: MagicMock) -> None:
        """Returns paginated list."""

        async def _run() -> None:
            pat = _mock_pat()
            count_result = MagicMock()
            count_result.scalar.return_value = 1
            scalars = MagicMock()
            scalars.all.return_value = [pat]
            list_result = MagicMock()
            list_result.scalars.return_value = scalars

            db = AsyncMock()
            db.execute.side_effect = [count_result, list_result]

            resp = await list_pats(db, user_id=None, scope=None, page=1, page_size=20)
            data = json.loads(bytes(resp.body))
            assert data["total"] == 1
            assert data["items"][0]["name"] == "CI Key"
            assert data["items"][0]["token_prefix"] == "shm_pat_abc"

        asyncio.run(_run())

    @patch("shomer.routes.admin_pats.require_scope")
    def test_empty_list(self, _: MagicMock) -> None:
        """Returns empty list."""

        async def _run() -> None:
            count_result = MagicMock()
            count_result.scalar.return_value = 0
            scalars = MagicMock()
            scalars.all.return_value = []
            list_result = MagicMock()
            list_result.scalars.return_value = scalars

            db = AsyncMock()
            db.execute.side_effect = [count_result, list_result]

            resp = await list_pats(db, user_id=None, scope=None, page=1, page_size=20)
            data = json.loads(bytes(resp.body))
            assert data["total"] == 0
            assert data["items"] == []

        asyncio.run(_run())

    @patch("shomer.routes.admin_pats.require_scope")
    def test_invalid_user_id_returns_400(self, _: MagicMock) -> None:
        """Returns 400 for invalid user_id."""

        async def _run() -> None:
            try:
                await list_pats(
                    AsyncMock(), user_id="bad", scope=None, page=1, page_size=20
                )
                raise AssertionError("Expected HTTPException")
            except HTTPException as exc:
                assert exc.status_code == 400

        asyncio.run(_run())


class TestGetPAT:
    """Tests for GET /admin/pats/{id}."""

    @patch("shomer.routes.admin_pats.require_scope")
    def test_returns_pat_detail(self, _: MagicMock) -> None:
        """Returns PAT details."""

        async def _run() -> None:
            pat = _mock_pat()
            result = MagicMock()
            result.scalar_one_or_none.return_value = pat
            db = AsyncMock()
            db.execute.return_value = result

            resp = await get_pat(str(pat.id), db)
            data = json.loads(bytes(resp.body))
            assert data["name"] == "CI Key"
            assert data["scopes"] == "admin:users:read"

        asyncio.run(_run())

    @patch("shomer.routes.admin_pats.require_scope")
    def test_invalid_uuid_returns_400(self, _: MagicMock) -> None:
        """Returns 400 for invalid UUID."""

        async def _run() -> None:
            try:
                await get_pat("bad", AsyncMock())
                raise AssertionError("Expected HTTPException")
            except HTTPException as exc:
                assert exc.status_code == 400

        asyncio.run(_run())

    @patch("shomer.routes.admin_pats.require_scope")
    def test_not_found_returns_404(self, _: MagicMock) -> None:
        """Returns 404."""

        async def _run() -> None:
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db = AsyncMock()
            db.execute.return_value = result
            try:
                await get_pat(str(uuid.uuid4()), db)
                raise AssertionError("Expected HTTPException")
            except HTTPException as exc:
                assert exc.status_code == 404

        asyncio.run(_run())


class TestRevokePAT:
    """Tests for DELETE /admin/pats/{id}."""

    @patch("shomer.routes.admin_pats.require_scope")
    def test_revokes_pat(self, _: MagicMock) -> None:
        """Revokes a PAT."""

        async def _run() -> None:
            pat = _mock_pat()
            result = MagicMock()
            result.scalar_one_or_none.return_value = pat
            db = AsyncMock()
            db.execute.return_value = result

            resp = await revoke_pat(str(pat.id), db)
            data = json.loads(bytes(resp.body))
            assert data["message"] == "PAT revoked successfully"
            assert pat.is_revoked is True
            db.flush.assert_awaited_once()

        asyncio.run(_run())

    @patch("shomer.routes.admin_pats.require_scope")
    def test_not_found_returns_404(self, _: MagicMock) -> None:
        """Returns 404."""

        async def _run() -> None:
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db = AsyncMock()
            db.execute.return_value = result
            try:
                await revoke_pat(str(uuid.uuid4()), db)
                raise AssertionError("Expected HTTPException")
            except HTTPException as exc:
                assert exc.status_code == 404

        asyncio.run(_run())

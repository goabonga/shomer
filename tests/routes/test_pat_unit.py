# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Pure unit tests for PAT route handlers."""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from shomer.routes.pat import create_pat, list_pats, revoke_pat
from shomer.services.pat_service import PATCreateResult, PATError, PATInfo


def _mock_user() -> MagicMock:
    u = MagicMock()
    u.user_id = uuid.uuid4()
    return u


class TestCreatePAT:
    """Unit tests for POST /api/pats."""

    def test_create_returns_201_with_token(self) -> None:
        async def _run() -> None:
            now = datetime.now(timezone.utc)
            mock_result = PATCreateResult(
                id=uuid.uuid4(),
                name="CI key",
                token="shm_pat_abcdef123456",
                token_prefix="shm_pat_abcdef1",
                scopes="api:read",
                expires_at=None,
                created_at=now,
            )

            with patch("shomer.routes.pat.PATService") as mock_cls:
                mock_svc = AsyncMock()
                mock_svc.create.return_value = mock_result
                mock_cls.return_value = mock_svc

                body = MagicMock(name="CI key", scopes="api:read", expires_at=None)
                resp = await create_pat(body, _mock_user(), AsyncMock())
                assert resp.status_code == 201
                data = json.loads(bytes(resp.body))
                assert data["token"] == "shm_pat_abcdef123456"
                assert data["name"] == "CI key"
                assert "Save this token" in data["message"]

        asyncio.run(_run())


class TestListPATs:
    """Unit tests for GET /api/pats."""

    def test_list_returns_metadata(self) -> None:
        async def _run() -> None:
            now = datetime.now(timezone.utc)
            mock_pats = [
                PATInfo(
                    id=uuid.uuid4(),
                    name="key-1",
                    token_prefix="shm_pat_abc",
                    scopes="api:read",
                    expires_at=None,
                    last_used_at=now,
                    last_used_ip="127.0.0.1",
                    use_count=5,
                    is_revoked=False,
                    created_at=now,
                ),
            ]

            with patch("shomer.routes.pat.PATService") as mock_cls:
                mock_svc = AsyncMock()
                mock_svc.list_for_user.return_value = mock_pats
                mock_cls.return_value = mock_svc

                resp = await list_pats(_mock_user(), AsyncMock())
                assert resp.status_code == 200
                data = json.loads(bytes(resp.body))
                assert len(data["tokens"]) == 1
                assert data["tokens"][0]["name"] == "key-1"
                assert "token" not in data["tokens"][0]

        asyncio.run(_run())

    def test_list_empty(self) -> None:
        async def _run() -> None:
            with patch("shomer.routes.pat.PATService") as mock_cls:
                mock_svc = AsyncMock()
                mock_svc.list_for_user.return_value = []
                mock_cls.return_value = mock_svc

                resp = await list_pats(_mock_user(), AsyncMock())
                data = json.loads(bytes(resp.body))
                assert data["tokens"] == []

        asyncio.run(_run())


class TestRevokePAT:
    """Unit tests for DELETE /api/pats/{id}."""

    def test_revoke_success(self) -> None:
        async def _run() -> None:
            with patch("shomer.routes.pat.PATService") as mock_cls:
                mock_svc = AsyncMock()
                mock_cls.return_value = mock_svc

                resp = await revoke_pat(uuid.uuid4(), _mock_user(), AsyncMock())
                assert resp.status_code == 200
                data = json.loads(bytes(resp.body))
                assert "revoked" in data["message"].lower()

        asyncio.run(_run())

    def test_revoke_not_found_returns_404(self) -> None:
        async def _run() -> None:
            with patch("shomer.routes.pat.PATService") as mock_cls:
                mock_svc = AsyncMock()
                mock_svc.revoke.side_effect = PATError("Token not found")
                mock_cls.return_value = mock_svc

                with pytest.raises(HTTPException) as exc_info:
                    await revoke_pat(uuid.uuid4(), _mock_user(), AsyncMock())
                assert exc_info.value.status_code == 404

        asyncio.run(_run())

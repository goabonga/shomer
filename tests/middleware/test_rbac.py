# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for RBAC middleware dependencies."""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from shomer.middleware.rbac import require_any_scope, require_scope


def _mock_user(
    user_id: str = "00000000-0000-0000-0000-000000000001",
    tenant_id: str | None = None,
) -> MagicMock:
    u = MagicMock()
    u.user_id = uuid.UUID(user_id)
    u.tenant_id = uuid.UUID(tenant_id) if tenant_id else None
    return u


class TestRequireScope:
    """Tests for require_scope dependency."""

    def test_allowed_passes(self) -> None:
        """User with the required scope passes."""

        async def _run() -> None:
            dep = require_scope("admin:users:read")
            mock_user = _mock_user()

            with (
                patch(
                    "shomer.middleware.rbac._resolve_user",
                    new_callable=AsyncMock,
                    return_value=mock_user,
                ),
                patch("shomer.services.rbac_service.RBACService") as mock_cls,
            ):
                mock_svc = AsyncMock()
                mock_svc.has_permission.return_value = True
                mock_cls.return_value = mock_svc

                await dep(MagicMock(), AsyncMock())
                mock_svc.has_permission.assert_awaited_once()

        asyncio.run(_run())

    def test_denied_raises_403(self) -> None:
        """User without the required scope gets 403."""

        async def _run() -> None:
            dep = require_scope("admin:users:delete")
            mock_user = _mock_user()

            with (
                patch(
                    "shomer.middleware.rbac._resolve_user",
                    new_callable=AsyncMock,
                    return_value=mock_user,
                ),
                patch("shomer.services.rbac_service.RBACService") as mock_cls,
            ):
                mock_svc = AsyncMock()
                mock_svc.has_permission.return_value = False
                mock_cls.return_value = mock_svc

                with pytest.raises(HTTPException) as exc_info:
                    await dep(MagicMock(), AsyncMock())
                assert exc_info.value.status_code == 403
                assert "admin:users:delete" in str(exc_info.value.detail)

        asyncio.run(_run())

    def test_passes_tenant_id(self) -> None:
        """Tenant ID from user context is passed to RBAC service."""

        async def _run() -> None:
            dep = require_scope("api:read")
            tid = "00000000-0000-0000-0000-000000000099"
            mock_user = _mock_user(tenant_id=tid)

            with (
                patch(
                    "shomer.middleware.rbac._resolve_user",
                    new_callable=AsyncMock,
                    return_value=mock_user,
                ),
                patch("shomer.services.rbac_service.RBACService") as mock_cls,
            ):
                mock_svc = AsyncMock()
                mock_svc.has_permission.return_value = True
                mock_cls.return_value = mock_svc

                await dep(MagicMock(), AsyncMock())
                call_kwargs = mock_svc.has_permission.call_args[1]
                assert call_kwargs["tenant_id"] == uuid.UUID(tid)

        asyncio.run(_run())


class TestRequireAnyScope:
    """Tests for require_any_scope dependency."""

    def test_one_match_passes(self) -> None:
        """User with at least one scope passes."""

        async def _run() -> None:
            dep = require_any_scope(["admin:read", "editor:write"])
            mock_user = _mock_user()

            with (
                patch(
                    "shomer.middleware.rbac._resolve_user",
                    new_callable=AsyncMock,
                    return_value=mock_user,
                ),
                patch("shomer.services.rbac_service.RBACService") as mock_cls,
            ):
                mock_svc = AsyncMock()
                mock_svc.has_any_permission.return_value = True
                mock_cls.return_value = mock_svc

                await dep(MagicMock(), AsyncMock())

        asyncio.run(_run())

    def test_no_match_raises_403(self) -> None:
        """User with no matching scope gets 403."""

        async def _run() -> None:
            dep = require_any_scope(["admin:read", "editor:write"])
            mock_user = _mock_user()

            with (
                patch(
                    "shomer.middleware.rbac._resolve_user",
                    new_callable=AsyncMock,
                    return_value=mock_user,
                ),
                patch("shomer.services.rbac_service.RBACService") as mock_cls,
            ):
                mock_svc = AsyncMock()
                mock_svc.has_any_permission.return_value = False
                mock_cls.return_value = mock_svc

                with pytest.raises(HTTPException) as exc_info:
                    await dep(MagicMock(), AsyncMock())
                assert exc_info.value.status_code == 403
                assert "admin:read" in str(exc_info.value.detail)

        asyncio.run(_run())

    def test_error_message_lists_scopes(self) -> None:
        """403 error message lists all required scopes."""

        async def _run() -> None:
            dep = require_any_scope(["x:a", "y:b"])
            mock_user = _mock_user()

            with (
                patch(
                    "shomer.middleware.rbac._resolve_user",
                    new_callable=AsyncMock,
                    return_value=mock_user,
                ),
                patch("shomer.services.rbac_service.RBACService") as mock_cls,
            ):
                mock_svc = AsyncMock()
                mock_svc.has_any_permission.return_value = False
                mock_cls.return_value = mock_svc

                with pytest.raises(HTTPException) as exc_info:
                    await dep(MagicMock(), AsyncMock())
                detail = str(exc_info.value.detail)
                assert "x:a" in detail
                assert "y:b" in detail

        asyncio.run(_run())


class TestResolveUser:
    """Tests for _resolve_user helper."""

    def test_unauthenticated_raises_401(self) -> None:
        async def _run() -> None:
            from shomer.middleware.rbac import _resolve_user

            with patch(
                "shomer.auth.get_current_user",
                new_callable=AsyncMock,
                side_effect=HTTPException(status_code=401, detail="Not authenticated"),
            ):
                with pytest.raises(HTTPException) as exc_info:
                    await _resolve_user(MagicMock(), AsyncMock())
                assert exc_info.value.status_code == 401

        asyncio.run(_run())

    def test_authenticated_returns_user(self) -> None:
        async def _run() -> None:
            from shomer.middleware.rbac import _resolve_user

            mock_user = _mock_user()
            with patch(
                "shomer.auth.get_current_user",
                new_callable=AsyncMock,
                return_value=mock_user,
            ):
                result = await _resolve_user(MagicMock(), AsyncMock())
                assert result.user_id == mock_user.user_id

        asyncio.run(_run())

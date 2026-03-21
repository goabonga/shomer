# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for RBACService."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

from shomer.services.rbac_service import RBACService


def _mock_user_role(
    *,
    role_id: uuid.UUID | None = None,
    tenant_id: uuid.UUID | None = None,
    expires_at: datetime | None = None,
) -> MagicMock:
    ur = MagicMock()
    ur.role_id = role_id or uuid.uuid4()
    ur.tenant_id = tenant_id
    ur.expires_at = expires_at
    return ur


class TestGetUserRoles:
    """Tests for resolving user roles."""

    def test_returns_global_roles(self) -> None:
        async def _run() -> None:
            ur = _mock_user_role()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [ur]
            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = RBACService(db)
            roles = await svc.get_user_roles(uuid.uuid4())
            assert len(roles) == 1

        asyncio.run(_run())

    def test_includes_tenant_specific_roles(self) -> None:
        async def _run() -> None:
            tid = uuid.uuid4()
            global_role = _mock_user_role()
            tenant_role = _mock_user_role(tenant_id=tid)
            other_tenant = _mock_user_role(tenant_id=uuid.uuid4())

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [
                global_role,
                tenant_role,
                other_tenant,
            ]
            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = RBACService(db)
            roles = await svc.get_user_roles(uuid.uuid4(), tenant_id=tid)
            assert len(roles) == 2  # global + matching tenant

        asyncio.run(_run())

    def test_excludes_expired_roles(self) -> None:
        async def _run() -> None:
            expired = _mock_user_role(
                expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
            )
            active = _mock_user_role(
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
            )
            no_expiry = _mock_user_role()

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [
                expired,
                active,
                no_expiry,
            ]
            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = RBACService(db)
            roles = await svc.get_user_roles(uuid.uuid4())
            assert len(roles) == 2  # active + no_expiry

        asyncio.run(_run())

    def test_empty_when_no_roles(self) -> None:
        async def _run() -> None:
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = RBACService(db)
            roles = await svc.get_user_roles(uuid.uuid4())
            assert roles == []

        asyncio.run(_run())


class TestGetUserScopes:
    """Tests for collecting scopes from user roles."""

    def test_returns_scopes_from_roles(self) -> None:
        async def _run() -> None:
            rid = uuid.uuid4()
            ur = _mock_user_role(role_id=rid)

            mock_roles_result = MagicMock()
            mock_roles_result.scalars.return_value.all.return_value = [ur]

            mock_scopes_result = MagicMock()
            mock_scopes_result.all.return_value = [
                ("admin:users:read",),
                ("admin:users:write",),
            ]

            db = AsyncMock()
            db.execute.side_effect = [mock_roles_result, mock_scopes_result]

            svc = RBACService(db)
            scopes = await svc.get_user_scopes(uuid.uuid4())
            assert scopes == {"admin:users:read", "admin:users:write"}

        asyncio.run(_run())

    def test_empty_when_no_roles(self) -> None:
        async def _run() -> None:
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = RBACService(db)
            scopes = await svc.get_user_scopes(uuid.uuid4())
            assert scopes == set()

        asyncio.run(_run())


class TestHasPermission:
    """Tests for has_permission with wildcard support."""

    def test_exact_match(self) -> None:
        async def _run() -> None:
            rid = uuid.uuid4()
            ur = _mock_user_role(role_id=rid)

            mock_roles_result = MagicMock()
            mock_roles_result.scalars.return_value.all.return_value = [ur]
            mock_scopes_result = MagicMock()
            mock_scopes_result.all.return_value = [("admin:users:read",)]

            db = AsyncMock()
            db.execute.side_effect = [mock_roles_result, mock_scopes_result]

            svc = RBACService(db)
            assert await svc.has_permission(uuid.uuid4(), "admin:users:read") is True

        asyncio.run(_run())

    def test_wildcard_match(self) -> None:
        async def _run() -> None:
            rid = uuid.uuid4()
            ur = _mock_user_role(role_id=rid)

            mock_roles_result = MagicMock()
            mock_roles_result.scalars.return_value.all.return_value = [ur]
            mock_scopes_result = MagicMock()
            mock_scopes_result.all.return_value = [("admin:*",)]

            db = AsyncMock()
            db.execute.side_effect = [mock_roles_result, mock_scopes_result]

            svc = RBACService(db)
            assert await svc.has_permission(uuid.uuid4(), "admin:users:read") is True

        asyncio.run(_run())

    def test_no_match(self) -> None:
        async def _run() -> None:
            rid = uuid.uuid4()
            ur = _mock_user_role(role_id=rid)

            mock_roles_result = MagicMock()
            mock_roles_result.scalars.return_value.all.return_value = [ur]
            mock_scopes_result = MagicMock()
            mock_scopes_result.all.return_value = [("editor:posts:read",)]

            db = AsyncMock()
            db.execute.side_effect = [mock_roles_result, mock_scopes_result]

            svc = RBACService(db)
            assert await svc.has_permission(uuid.uuid4(), "admin:users:read") is False

        asyncio.run(_run())

    def test_star_matches_all(self) -> None:
        async def _run() -> None:
            rid = uuid.uuid4()
            ur = _mock_user_role(role_id=rid)

            mock_roles_result = MagicMock()
            mock_roles_result.scalars.return_value.all.return_value = [ur]
            mock_scopes_result = MagicMock()
            mock_scopes_result.all.return_value = [("*",)]

            db = AsyncMock()
            db.execute.side_effect = [mock_roles_result, mock_scopes_result]

            svc = RBACService(db)
            assert await svc.has_permission(uuid.uuid4(), "anything:here") is True

        asyncio.run(_run())

    def test_expired_role_not_matched(self) -> None:
        async def _run() -> None:
            expired = _mock_user_role(
                expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
            )

            mock_roles_result = MagicMock()
            mock_roles_result.scalars.return_value.all.return_value = [expired]

            db = AsyncMock()
            db.execute.return_value = mock_roles_result

            svc = RBACService(db)
            assert await svc.has_permission(uuid.uuid4(), "admin:users:read") is False

        asyncio.run(_run())


class TestHasAnyPermission:
    """Tests for has_any_permission."""

    def test_matches_one_of_many(self) -> None:
        async def _run() -> None:
            rid = uuid.uuid4()
            ur = _mock_user_role(role_id=rid)

            mock_roles_result = MagicMock()
            mock_roles_result.scalars.return_value.all.return_value = [ur]
            mock_scopes_result = MagicMock()
            mock_scopes_result.all.return_value = [("editor:posts:write",)]

            db = AsyncMock()
            db.execute.side_effect = [mock_roles_result, mock_scopes_result]

            svc = RBACService(db)
            result = await svc.has_any_permission(
                uuid.uuid4(),
                ["admin:users:read", "editor:posts:write"],
            )
            assert result is True

        asyncio.run(_run())

    def test_no_match_returns_false(self) -> None:
        async def _run() -> None:
            rid = uuid.uuid4()
            ur = _mock_user_role(role_id=rid)

            mock_roles_result = MagicMock()
            mock_roles_result.scalars.return_value.all.return_value = [ur]
            mock_scopes_result = MagicMock()
            mock_scopes_result.all.return_value = [("viewer:*",)]

            db = AsyncMock()
            db.execute.side_effect = [mock_roles_result, mock_scopes_result]

            svc = RBACService(db)
            result = await svc.has_any_permission(
                uuid.uuid4(),
                ["admin:users:read", "editor:posts:write"],
            )
            assert result is False

        asyncio.run(_run())


class TestScopeMatches:
    """Tests for static scope_matches method."""

    def test_exact_match(self) -> None:
        assert RBACService.scope_matches("admin:users:read", "admin:users:read") is True

    def test_no_match(self) -> None:
        assert (
            RBACService.scope_matches("admin:users:read", "admin:users:write") is False
        )

    def test_wildcard_star(self) -> None:
        assert RBACService.scope_matches("admin:*", "admin:users:read") is True

    def test_wildcard_all(self) -> None:
        assert RBACService.scope_matches("*", "anything") is True

    def test_wildcard_partial(self) -> None:
        assert RBACService.scope_matches("admin:users:*", "admin:users:read") is True

    def test_wildcard_no_match(self) -> None:
        assert RBACService.scope_matches("editor:*", "admin:users:read") is False

    def test_no_wildcard_no_match(self) -> None:
        assert RBACService.scope_matches("admin", "admin:users") is False


class TestMatchesAny:
    """Tests for static _matches_any method."""

    def test_exact(self) -> None:
        assert RBACService._matches_any("a:b", {"a:b", "c:d"}) is True

    def test_wildcard(self) -> None:
        assert RBACService._matches_any("a:b:c", {"a:*"}) is True

    def test_no_match(self) -> None:
        assert RBACService._matches_any("x:y", {"a:b"}) is False

    def test_empty_available(self) -> None:
        assert RBACService._matches_any("a:b", set()) is False

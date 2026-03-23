# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for admin roles and scopes API routes."""

from __future__ import annotations

import asyncio
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from shomer.routes.admin_roles_scopes import (
    assign_role_to_user,
    assign_scope_to_role,
    create_role,
    create_scope,
    delete_role,
    delete_scope,
    list_roles,
    list_scopes,
    remove_role_from_user,
    update_scope,
)


def _mock_scope(name: str = "admin:users:read") -> MagicMock:
    """Create a mock Scope."""
    s = MagicMock()
    s.id = uuid.uuid4()
    s.name = name
    s.description = f"Description for {name}"
    return s


def _mock_role(name: str = "admin", is_system: bool = False) -> MagicMock:
    """Create a mock Role."""
    r = MagicMock()
    r.id = uuid.uuid4()
    r.name = name
    r.description = "Admin role"
    r.is_system = is_system
    r.scopes = [_mock_scope()]
    return r


class TestListScopes:
    """Tests for GET /admin/scopes."""

    @patch("shomer.routes.admin_roles_scopes.require_scope")
    def test_returns_scopes(self, _: MagicMock) -> None:
        """Returns list of scopes."""

        async def _run() -> None:
            s = _mock_scope()
            scalars = MagicMock()
            scalars.all.return_value = [s]
            result = MagicMock()
            result.scalars.return_value = scalars
            db = AsyncMock()
            db.execute.return_value = result

            resp = await list_scopes(db)
            data = json.loads(bytes(resp.body))
            assert data["total"] == 1
            assert data["items"][0]["name"] == "admin:users:read"

        asyncio.run(_run())


class TestCreateScope:
    """Tests for POST /admin/scopes."""

    @patch("shomer.routes.admin_roles_scopes.require_scope")
    def test_creates_scope(self, _: MagicMock) -> None:
        """Creates a new scope."""

        async def _run() -> None:
            check_result = MagicMock()
            check_result.scalar_one_or_none.return_value = None
            db = AsyncMock()
            db.execute.return_value = check_result

            from shomer.routes.admin_roles_scopes import ScopeRequest

            body = ScopeRequest(name="test:scope", description="Test")
            resp = await create_scope(body, db)
            assert resp.status_code == 201
            data = json.loads(bytes(resp.body))
            assert data["name"] == "test:scope"
            assert data["message"] == "Scope created successfully"

        asyncio.run(_run())

    @patch("shomer.routes.admin_roles_scopes.require_scope")
    def test_duplicate_returns_409(self, _: MagicMock) -> None:
        """Returns 409 for duplicate scope."""

        async def _run() -> None:
            check_result = MagicMock()
            check_result.scalar_one_or_none.return_value = MagicMock()
            db = AsyncMock()
            db.execute.return_value = check_result

            from shomer.routes.admin_roles_scopes import ScopeRequest

            body = ScopeRequest(name="dup:scope")
            try:
                await create_scope(body, db)
                raise AssertionError("Expected HTTPException")
            except HTTPException as exc:
                assert exc.status_code == 409

        asyncio.run(_run())


class TestUpdateScope:
    """Tests for PUT /admin/scopes/{id}."""

    @patch("shomer.routes.admin_roles_scopes.require_scope")
    def test_updates_scope(self, _: MagicMock) -> None:
        """Updates scope name."""

        async def _run() -> None:
            s = _mock_scope()
            result = MagicMock()
            result.scalar_one_or_none.return_value = s
            db = AsyncMock()
            db.execute.return_value = result

            from shomer.routes.admin_roles_scopes import ScopeRequest

            body = ScopeRequest(name="updated:scope")
            resp = await update_scope(str(s.id), body, db)
            data = json.loads(bytes(resp.body))
            assert data["name"] == "updated:scope"

        asyncio.run(_run())


class TestDeleteScope:
    """Tests for DELETE /admin/scopes/{id}."""

    @patch("shomer.routes.admin_roles_scopes.require_scope")
    def test_deletes_scope(self, _: MagicMock) -> None:
        """Deletes a scope."""

        async def _run() -> None:
            s = _mock_scope()
            result = MagicMock()
            result.scalar_one_or_none.return_value = s
            db = AsyncMock()
            db.execute.return_value = result

            resp = await delete_scope(str(s.id), db)
            data = json.loads(bytes(resp.body))
            assert data["message"] == "Scope deleted successfully"
            db.delete.assert_awaited_once_with(s)

        asyncio.run(_run())


class TestListRoles:
    """Tests for GET /admin/roles."""

    @patch("shomer.routes.admin_roles_scopes.require_scope")
    def test_returns_roles_with_scopes(self, _: MagicMock) -> None:
        """Returns roles with scope names."""

        async def _run() -> None:
            r = _mock_role()
            scalars = MagicMock()
            scalars.all.return_value = [r]
            result = MagicMock()
            result.scalars.return_value = scalars
            db = AsyncMock()
            db.execute.return_value = result

            resp = await list_roles(db)
            data = json.loads(bytes(resp.body))
            assert data["total"] == 1
            assert data["items"][0]["name"] == "admin"
            assert len(data["items"][0]["scopes"]) == 1

        asyncio.run(_run())


class TestCreateRole:
    """Tests for POST /admin/roles."""

    @patch("shomer.routes.admin_roles_scopes.require_scope")
    def test_creates_role(self, _: MagicMock) -> None:
        """Creates a new role."""

        async def _run() -> None:
            check_result = MagicMock()
            check_result.scalar_one_or_none.return_value = None
            db = AsyncMock()
            db.execute.return_value = check_result

            from shomer.routes.admin_roles_scopes import RoleRequest

            body = RoleRequest(name="editor", description="Editor role")
            resp = await create_role(body, db)
            assert resp.status_code == 201
            data = json.loads(bytes(resp.body))
            assert data["name"] == "editor"

        asyncio.run(_run())


class TestDeleteRole:
    """Tests for DELETE /admin/roles/{id}."""

    @patch("shomer.routes.admin_roles_scopes.require_scope")
    def test_cannot_delete_system_role(self, _: MagicMock) -> None:
        """Returns 400 for system role."""

        async def _run() -> None:
            r = _mock_role(is_system=True)
            result = MagicMock()
            result.scalar_one_or_none.return_value = r
            db = AsyncMock()
            db.execute.return_value = result

            try:
                await delete_role(str(r.id), db)
                raise AssertionError("Expected HTTPException")
            except HTTPException as exc:
                assert exc.status_code == 400

        asyncio.run(_run())

    @patch("shomer.routes.admin_roles_scopes.require_scope")
    def test_deletes_non_system_role(self, _: MagicMock) -> None:
        """Deletes a non-system role."""

        async def _run() -> None:
            r = _mock_role(is_system=False)
            result = MagicMock()
            result.scalar_one_or_none.return_value = r
            db = AsyncMock()
            db.execute.return_value = result

            resp = await delete_role(str(r.id), db)
            data = json.loads(bytes(resp.body))
            assert data["message"] == "Role deleted successfully"

        asyncio.run(_run())


class TestAssignScopeToRole:
    """Tests for POST /admin/roles/{id}/scopes/{scope_id}."""

    @patch("shomer.routes.admin_roles_scopes.require_scope")
    def test_assigns_scope(self, _: MagicMock) -> None:
        """Assigns a scope to a role."""

        async def _run() -> None:
            role_result = MagicMock()
            role_result.scalar_one_or_none.return_value = MagicMock()
            scope_result = MagicMock()
            scope_result.scalar_one_or_none.return_value = MagicMock()
            existing_result = MagicMock()
            existing_result.scalar_one_or_none.return_value = None

            db = AsyncMock()
            db.execute.side_effect = [role_result, scope_result, existing_result]

            resp = await assign_scope_to_role(str(uuid.uuid4()), str(uuid.uuid4()), db)
            assert resp.status_code == 201

        asyncio.run(_run())


class TestAssignRoleToUser:
    """Tests for POST /admin/users/{id}/roles/{role_id}."""

    @patch("shomer.routes.admin_roles_scopes.require_scope")
    def test_assigns_role(self, _: MagicMock) -> None:
        """Assigns a role to a user."""

        async def _run() -> None:
            user_result = MagicMock()
            user_result.scalar_one_or_none.return_value = MagicMock()
            role_result = MagicMock()
            role_result.scalar_one_or_none.return_value = MagicMock()
            existing_result = MagicMock()
            existing_result.scalar_one_or_none.return_value = None

            db = AsyncMock()
            db.execute.side_effect = [user_result, role_result, existing_result]

            resp = await assign_role_to_user(str(uuid.uuid4()), str(uuid.uuid4()), db)
            assert resp.status_code == 201

        asyncio.run(_run())

    @patch("shomer.routes.admin_roles_scopes.require_scope")
    def test_user_not_found_returns_404(self, _: MagicMock) -> None:
        """Returns 404 when user not found."""

        async def _run() -> None:
            user_result = MagicMock()
            user_result.scalar_one_or_none.return_value = None

            db = AsyncMock()
            db.execute.return_value = user_result

            try:
                await assign_role_to_user(str(uuid.uuid4()), str(uuid.uuid4()), db)
                raise AssertionError("Expected HTTPException")
            except HTTPException as exc:
                assert exc.status_code == 404

        asyncio.run(_run())


class TestRemoveRoleFromUser:
    """Tests for DELETE /admin/users/{id}/roles/{role_id}."""

    @patch("shomer.routes.admin_roles_scopes.require_scope")
    def test_removes_role(self, _: MagicMock) -> None:
        """Removes a role from a user."""

        async def _run() -> None:
            ur = MagicMock()
            result = MagicMock()
            result.scalar_one_or_none.return_value = ur
            db = AsyncMock()
            db.execute.return_value = result

            resp = await remove_role_from_user(str(uuid.uuid4()), str(uuid.uuid4()), db)
            data = json.loads(bytes(resp.body))
            assert data["message"] == "Role removed from user"
            db.delete.assert_awaited_once_with(ur)

        asyncio.run(_run())

    @patch("shomer.routes.admin_roles_scopes.require_scope")
    def test_not_found_returns_404(self, _: MagicMock) -> None:
        """Returns 404 when assignment not found."""

        async def _run() -> None:
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db = AsyncMock()
            db.execute.return_value = result

            try:
                await remove_role_from_user(str(uuid.uuid4()), str(uuid.uuid4()), db)
                raise AssertionError("Expected HTTPException")
            except HTTPException as exc:
                assert exc.status_code == 404

        asyncio.run(_run())

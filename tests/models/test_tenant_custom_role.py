# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for TenantCustomRole model."""

import uuid

from shomer.models.tenant_custom_role import TenantCustomRole


class TestTenantCustomRoleModel:
    """Tests for TenantCustomRole SQLAlchemy model definition."""

    def test_tablename(self) -> None:
        assert TenantCustomRole.__tablename__ == "tenant_custom_roles"

    def test_required_fields(self) -> None:
        tid = uuid.uuid4()
        r = TenantCustomRole(
            tenant_id=tid,
            name="editor",
            permissions=["posts:read", "posts:write"],
        )
        assert r.tenant_id == tid
        assert r.name == "editor"
        assert r.permissions == ["posts:read", "posts:write"]

    def test_tenant_id_indexed(self) -> None:
        col = TenantCustomRole.__table__.c.tenant_id
        assert col.index is True

    def test_unique_constraint(self) -> None:
        names = [c.name for c in getattr(TenantCustomRole.__table__, "constraints", [])]
        assert "uq_tenant_role_name" in names

    def test_empty_permissions(self) -> None:
        r = TenantCustomRole(
            tenant_id=uuid.uuid4(),
            name="viewer",
            permissions=[],
        )
        assert r.permissions == []

    def test_repr(self) -> None:
        tid = uuid.uuid4()
        r = TenantCustomRole(tenant_id=tid, name="admin", permissions=[])
        rep = repr(r)
        assert str(tid) in rep
        assert "admin" in rep

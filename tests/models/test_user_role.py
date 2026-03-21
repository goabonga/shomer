# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for UserRole model."""

import uuid
from datetime import datetime, timezone

from shomer.models.user_role import UserRole


class TestUserRoleModel:
    """Tests for UserRole SQLAlchemy model definition."""

    def test_tablename(self) -> None:
        assert UserRole.__tablename__ == "user_roles"

    def test_required_fields(self) -> None:
        uid = uuid.uuid4()
        rid = uuid.uuid4()
        ur = UserRole(user_id=uid, role_id=rid)
        assert ur.user_id == uid
        assert ur.role_id == rid
        assert ur.tenant_id is None
        assert ur.expires_at is None

    def test_with_tenant(self) -> None:
        tid = uuid.uuid4()
        ur = UserRole(user_id=uuid.uuid4(), role_id=uuid.uuid4(), tenant_id=tid)
        assert ur.tenant_id == tid

    def test_with_expiration(self) -> None:
        now = datetime.now(timezone.utc)
        ur = UserRole(user_id=uuid.uuid4(), role_id=uuid.uuid4(), expires_at=now)
        assert ur.expires_at == now

    def test_user_id_indexed(self) -> None:
        col = UserRole.__table__.c.user_id
        assert col.index is True

    def test_role_id_indexed(self) -> None:
        col = UserRole.__table__.c.role_id
        assert col.index is True

    def test_tenant_id_indexed(self) -> None:
        col = UserRole.__table__.c.tenant_id
        assert col.index is True

    def test_unique_constraint(self) -> None:
        names = [c.name for c in getattr(UserRole.__table__, "constraints", [])]
        assert "uq_user_role_tenant" in names

    def test_repr(self) -> None:
        uid = uuid.uuid4()
        rid = uuid.uuid4()
        ur = UserRole(user_id=uid, role_id=rid)
        r = repr(ur)
        assert str(uid) in r
        assert str(rid) in r

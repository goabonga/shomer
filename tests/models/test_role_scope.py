# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for RoleScope model."""

import uuid

from shomer.models.role_scope import RoleScope


class TestRoleScopeModel:
    """Tests for RoleScope SQLAlchemy model definition."""

    def test_tablename(self) -> None:
        assert RoleScope.__tablename__ == "role_scopes"

    def test_required_fields(self) -> None:
        rid = uuid.uuid4()
        sid = uuid.uuid4()
        rs = RoleScope(role_id=rid, scope_id=sid)
        assert rs.role_id == rid
        assert rs.scope_id == sid

    def test_role_id_indexed(self) -> None:
        col = RoleScope.__table__.c.role_id
        assert col.index is True

    def test_scope_id_indexed(self) -> None:
        col = RoleScope.__table__.c.scope_id
        assert col.index is True

    def test_unique_constraint(self) -> None:
        names = [c.name for c in getattr(RoleScope.__table__, "constraints", [])]
        assert "uq_role_scope" in names

    def test_repr(self) -> None:
        rid = uuid.uuid4()
        sid = uuid.uuid4()
        rs = RoleScope(role_id=rid, scope_id=sid)
        r = repr(rs)
        assert str(rid) in r
        assert str(sid) in r

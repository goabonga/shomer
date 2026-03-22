# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for TenantMember model."""

import uuid
from datetime import datetime, timezone

from shomer.models.tenant_member import TenantMember


class TestTenantMemberModel:
    """Tests for TenantMember SQLAlchemy model definition."""

    def test_tablename(self) -> None:
        assert TenantMember.__tablename__ == "tenant_members"

    def test_required_fields(self) -> None:
        uid = uuid.uuid4()
        tid = uuid.uuid4()
        now = datetime.now(timezone.utc)
        tm = TenantMember(
            user_id=uid,
            tenant_id=tid,
            role="admin",
            joined_at=now,
        )
        assert tm.user_id == uid
        assert tm.tenant_id == tid
        assert tm.role == "admin"
        assert tm.joined_at == now

    def test_user_id_indexed(self) -> None:
        col = TenantMember.__table__.c.user_id
        assert col.index is True

    def test_tenant_id_indexed(self) -> None:
        col = TenantMember.__table__.c.tenant_id
        assert col.index is True

    def test_unique_constraint(self) -> None:
        names = [c.name for c in getattr(TenantMember.__table__, "constraints", [])]
        assert "uq_tenant_member" in names

    def test_repr(self) -> None:
        uid = uuid.uuid4()
        tid = uuid.uuid4()
        tm = TenantMember(
            user_id=uid,
            tenant_id=tid,
            role="member",
            joined_at=datetime.now(timezone.utc),
        )
        r = repr(tm)
        assert str(uid) in r
        assert str(tid) in r
        assert "member" in r

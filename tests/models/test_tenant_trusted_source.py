# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for TenantTrustedSource model."""

import uuid

from shomer.models.tenant_trusted_source import TenantTrustedSource


class TestTenantTrustedSourceModel:
    """Tests for TenantTrustedSource SQLAlchemy model definition."""

    def test_tablename(self) -> None:
        assert TenantTrustedSource.__tablename__ == "tenant_trusted_sources"

    def test_required_fields(self) -> None:
        tid = uuid.uuid4()
        ttid = uuid.uuid4()
        s = TenantTrustedSource(tenant_id=tid, trusted_tenant_id=ttid)
        assert s.tenant_id == tid
        assert s.trusted_tenant_id == ttid
        assert s.description is None

    def test_with_description(self) -> None:
        s = TenantTrustedSource(
            tenant_id=uuid.uuid4(),
            trusted_tenant_id=uuid.uuid4(),
            description="Trust Acme users",
        )
        assert s.description == "Trust Acme users"

    def test_unique_constraint(self) -> None:
        names = [
            c.name for c in getattr(TenantTrustedSource.__table__, "constraints", [])
        ]
        assert "uq_tenant_trusted_source" in names

    def test_tenant_id_indexed(self) -> None:
        col = TenantTrustedSource.__table__.c.tenant_id
        assert col.index is True

    def test_repr(self) -> None:
        tid = uuid.uuid4()
        ttid = uuid.uuid4()
        s = TenantTrustedSource(tenant_id=tid, trusted_tenant_id=ttid)
        r = repr(s)
        assert str(tid) in r
        assert str(ttid) in r

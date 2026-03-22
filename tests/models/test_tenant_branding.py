# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for TenantBranding model."""

import uuid

from shomer.models.tenant_branding import TenantBranding


class TestTenantBrandingModel:
    """Tests for TenantBranding SQLAlchemy model definition."""

    def test_tablename(self) -> None:
        assert TenantBranding.__tablename__ == "tenant_brandings"

    def test_required_fields(self) -> None:
        tid = uuid.uuid4()
        b = TenantBranding(tenant_id=tid)
        assert b.tenant_id == tid
        assert b.logo_url is None
        assert b.favicon_url is None
        assert b.primary_color is None
        assert b.custom_css is None

    def test_with_all_fields(self) -> None:
        b = TenantBranding(
            tenant_id=uuid.uuid4(),
            logo_url="https://acme.com/logo.png",
            favicon_url="https://acme.com/favicon.ico",
            primary_color="#1a73e8",
            secondary_color="#666666",
            custom_css="body { font-family: Arial; }",
        )
        assert b.logo_url == "https://acme.com/logo.png"
        assert b.primary_color == "#1a73e8"
        assert b.custom_css == "body { font-family: Arial; }"

    def test_tenant_id_unique(self) -> None:
        col = TenantBranding.__table__.c.tenant_id
        assert col.unique is True

    def test_tenant_id_indexed(self) -> None:
        col = TenantBranding.__table__.c.tenant_id
        assert col.index is True

    def test_repr(self) -> None:
        tid = uuid.uuid4()
        b = TenantBranding(tenant_id=tid)
        assert str(tid) in repr(b)

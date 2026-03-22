# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for TenantBranding model."""

import uuid

from shomer.models.tenant_branding import TenantBranding


class TestTenantBrandingModel:
    """Tests for TenantBranding SQLAlchemy model definition."""

    def test_tablename(self) -> None:
        assert TenantBranding.__tablename__ == "tenant_brandings"

    def test_minimal_fields(self) -> None:
        tid = uuid.uuid4()
        b = TenantBranding(tenant_id=tid, show_powered_by=True)
        assert b.tenant_id == tid
        assert b.logo_url is None
        assert b.logo_dark_url is None
        assert b.favicon_url is None
        assert b.primary_color is None
        assert b.custom_css is None
        assert b.custom_js is None
        assert b.font_family is None
        assert b.font_url is None
        assert b.show_powered_by is True

    def test_full_branding(self) -> None:
        b = TenantBranding(
            tenant_id=uuid.uuid4(),
            logo_url="https://acme.com/logo.png",
            logo_dark_url="https://acme.com/logo-dark.png",
            favicon_url="https://acme.com/favicon.ico",
            primary_color="#e94560",
            secondary_color="#0f3460",
            accent_color="#e94560",
            background_color="#1a1a2e",
            surface_color="#16213e",
            text_color="#e0e0e0",
            text_muted_color="#a0a0a0",
            error_color="#ff6b6b",
            success_color="#00b894",
            border_color="#0f3460",
            warning_color="#fdcb6e",
            info_color="#74b9ff",
            font_family="'Inter', sans-serif",
            font_url="https://fonts.googleapis.com/css2?family=Inter",
            custom_css="h1 { color: red; }",
            custom_js="console.log('hi');",
            show_powered_by=False,
        )
        assert b.logo_dark_url == "https://acme.com/logo-dark.png"
        assert b.accent_color == "#e94560"
        assert b.background_color == "#1a1a2e"
        assert b.text_color == "#e0e0e0"
        assert b.font_family == "'Inter', sans-serif"
        assert b.custom_js == "console.log('hi');"
        assert b.show_powered_by is False

    def test_tenant_id_unique(self) -> None:
        col = TenantBranding.__table__.c.tenant_id
        assert col.unique is True

    def test_tenant_id_indexed(self) -> None:
        col = TenantBranding.__table__.c.tenant_id
        assert col.index is True

    def test_repr(self) -> None:
        tid = uuid.uuid4()
        b = TenantBranding(tenant_id=tid, show_powered_by=True)
        assert str(tid) in repr(b)

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for Tenant model."""

from shomer.models.tenant import Tenant


class TestTenantModel:
    """Tests for Tenant SQLAlchemy model definition."""

    def test_tablename(self) -> None:
        assert Tenant.__tablename__ == "tenants"

    def test_required_fields(self) -> None:
        t = Tenant(slug="acme-corp", name="Acme Corp", is_active=True, settings={})
        assert t.slug == "acme-corp"
        assert t.name == "Acme Corp"
        assert t.is_active is True
        assert t.settings == {}
        assert t.custom_domain is None

    def test_with_custom_domain(self) -> None:
        t = Tenant(
            slug="acme",
            name="Acme",
            custom_domain="auth.acme.com",
            is_active=True,
            settings={},
        )
        assert t.custom_domain == "auth.acme.com"

    def test_slug_unique(self) -> None:
        col = Tenant.__table__.c.slug
        assert col.unique is True

    def test_slug_indexed(self) -> None:
        col = Tenant.__table__.c.slug
        assert col.index is True

    def test_custom_domain_unique(self) -> None:
        col = Tenant.__table__.c.custom_domain
        assert col.unique is True

    def test_custom_domain_indexed(self) -> None:
        col = Tenant.__table__.c.custom_domain
        assert col.index is True

    def test_settings_json(self) -> None:
        t = Tenant(
            slug="test",
            name="Test",
            settings={"theme": "dark", "features": ["sso"]},
            is_active=True,
        )
        assert t.settings["theme"] == "dark"

    def test_repr(self) -> None:
        t = Tenant(slug="acme", name="Acme Corp", is_active=True, settings={})
        r = repr(t)
        assert "acme" in r
        assert "Acme Corp" in r

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for TenantTemplate model."""

import uuid

from shomer.models.tenant_template import TenantTemplate


class TestTenantTemplateModel:
    """Tests for TenantTemplate SQLAlchemy model definition."""

    def test_tablename(self) -> None:
        assert TenantTemplate.__tablename__ == "tenant_templates"

    def test_required_fields(self) -> None:
        tid = uuid.uuid4()
        t = TenantTemplate(
            tenant_id=tid,
            template_name="auth/login.html",
            content="<h1>Custom Login</h1>",
            is_active=True,
        )
        assert t.tenant_id == tid
        assert t.template_name == "auth/login.html"
        assert t.content == "<h1>Custom Login</h1>"
        assert t.is_active is True
        assert t.description is None

    def test_with_description(self) -> None:
        t = TenantTemplate(
            tenant_id=uuid.uuid4(),
            template_name="oauth2/consent.html",
            content="<p>Custom consent</p>",
            description="Custom consent page for Acme",
            is_active=True,
        )
        assert t.description == "Custom consent page for Acme"

    def test_inactive_template(self) -> None:
        t = TenantTemplate(
            tenant_id=uuid.uuid4(),
            template_name="auth/register.html",
            content="<p>Draft</p>",
            is_active=False,
        )
        assert t.is_active is False

    def test_tenant_id_indexed(self) -> None:
        col = TenantTemplate.__table__.c.tenant_id
        assert col.index is True

    def test_unique_constraint(self) -> None:
        names = [c.name for c in getattr(TenantTemplate.__table__, "constraints", [])]
        assert "uq_tenant_template_name" in names

    def test_repr(self) -> None:
        tid = uuid.uuid4()
        t = TenantTemplate(
            tenant_id=tid,
            template_name="oauth2/consent.html",
            content="",
            is_active=True,
        )
        r = repr(t)
        assert str(tid) in r
        assert "oauth2/consent.html" in r

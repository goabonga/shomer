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
            template_type="login",
            template_content="<h1>Custom Login</h1>",
        )
        assert t.tenant_id == tid
        assert t.template_type == "login"
        assert t.template_content == "<h1>Custom Login</h1>"

    def test_tenant_id_indexed(self) -> None:
        col = TenantTemplate.__table__.c.tenant_id
        assert col.index is True

    def test_unique_constraint(self) -> None:
        names = [c.name for c in getattr(TenantTemplate.__table__, "constraints", [])]
        assert "uq_tenant_template_type" in names

    def test_repr(self) -> None:
        tid = uuid.uuid4()
        t = TenantTemplate(tenant_id=tid, template_type="consent", template_content="")
        r = repr(t)
        assert str(tid) in r
        assert "consent" in r

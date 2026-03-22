# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""TenantTemplate model for custom email and page templates."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from shomer.models.tenant import Tenant

from shomer.core.database import Base, TimestampMixin, UUIDMixin


class TenantTemplate(Base, UUIDMixin, TimestampMixin):
    """Custom template override for a tenant.

    Allows tenants to provide custom Jinja2 content for specific
    templates. Templates can be deactivated without deletion via
    ``is_active``.

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    tenant_id : uuid.UUID
        Foreign key to the tenant.
    template_name : str
        Template path matching the filesystem layout
        (e.g. ``auth/login.html``, ``emails/mjml/password_reset.mjml``).
    content : str
        Jinja2 template content.
    description : str or None
        Human-readable description of the customization.
    is_active : bool
        Whether this override is active.
    tenant : Tenant
        The associated tenant.
    created_at : datetime
        Row creation timestamp (from TimestampMixin).
    updated_at : datetime
        Last update timestamp (from TimestampMixin).
    """

    __tablename__ = "tenant_templates"
    __table_args__ = (
        UniqueConstraint("tenant_id", "template_name", name="uq_tenant_template_name"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    template_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    tenant: Mapped[Tenant] = relationship()

    def __repr__(self) -> str:
        return f"<TenantTemplate tenant_id={self.tenant_id} name={self.template_name}>"

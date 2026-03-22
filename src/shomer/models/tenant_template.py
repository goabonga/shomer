# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""TenantTemplate model for custom email and page templates."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from shomer.models.tenant import Tenant

from shomer.core.database import Base, TimestampMixin, UUIDMixin


class TenantTemplate(Base, UUIDMixin, TimestampMixin):
    """Custom template override for a tenant.

    Allows tenants to provide custom Jinja2 content for specific
    template types (login page, email verification, etc.).

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    tenant_id : uuid.UUID
        Foreign key to the tenant.
    template_type : str
        Template identifier (e.g. ``login``, ``consent``,
        ``email_verification``, ``email_password_reset``).
    template_content : str
        Jinja2 template content.
    tenant : Tenant
        The associated tenant.
    created_at : datetime
        Row creation timestamp (from TimestampMixin).
    updated_at : datetime
        Last update timestamp (from TimestampMixin).
    """

    __tablename__ = "tenant_templates"
    __table_args__ = (
        UniqueConstraint("tenant_id", "template_type", name="uq_tenant_template_type"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    template_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    template_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Relationships
    tenant: Mapped[Tenant] = relationship()

    def __repr__(self) -> str:
        return f"<TenantTemplate tenant_id={self.tenant_id} type={self.template_type}>"

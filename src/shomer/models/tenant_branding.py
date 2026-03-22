# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""TenantBranding model for tenant visual customization."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from shomer.models.tenant import Tenant

from shomer.core.database import Base, TimestampMixin, UUIDMixin


class TenantBranding(Base, UUIDMixin, TimestampMixin):
    """Visual branding configuration for a tenant.

    Controls the look and feel of auth pages (login, consent, error)
    and emails for the tenant.

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    tenant_id : uuid.UUID
        Foreign key to the tenant (one-to-one).
    logo_url : str or None
        URL to the tenant's logo image.
    favicon_url : str or None
        URL to the tenant's favicon.
    primary_color : str or None
        Primary brand color (hex, e.g. ``#1a73e8``).
    secondary_color : str or None
        Secondary brand color (hex).
    custom_css : str or None
        Raw CSS injected into auth pages.
    tenant : Tenant
        The associated tenant.
    created_at : datetime
        Row creation timestamp (from TimestampMixin).
    updated_at : datetime
        Last update timestamp (from TimestampMixin).
    """

    __tablename__ = "tenant_brandings"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    logo_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )
    favicon_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )
    primary_color: Mapped[str | None] = mapped_column(
        String(7),
        nullable=True,
    )
    secondary_color: Mapped[str | None] = mapped_column(
        String(7),
        nullable=True,
    )
    custom_css: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    tenant: Mapped[Tenant] = relationship()

    def __repr__(self) -> str:
        return f"<TenantBranding tenant_id={self.tenant_id}>"

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""TenantTrustedSource model for inter-tenant trust policies."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from shomer.models.tenant import Tenant

from shomer.core.database import Base, TimestampMixin, UUIDMixin


class TenantTrustedSource(Base, UUIDMixin, TimestampMixin):
    """A trusted source tenant for cross-tenant access.

    When a tenant's ``trust_mode`` is ``SPECIFIC``, only users
    registered on tenants listed here (or explicit members) can
    access the tenant.

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    tenant_id : uuid.UUID
        The tenant that defines this trust rule.
    trusted_tenant_id : uuid.UUID
        The tenant whose users are trusted.
    description : str or None
        Human-readable description of the trust relationship.
    tenant : Tenant
        The owning tenant.
    trusted_tenant : Tenant
        The trusted source tenant.
    created_at : datetime
        Row creation timestamp (from TimestampMixin).
    updated_at : datetime
        Last update timestamp (from TimestampMixin).
    """

    __tablename__ = "tenant_trusted_sources"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "trusted_tenant_id", name="uq_tenant_trusted_source"
        ),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    trusted_tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    tenant: Mapped[Tenant] = relationship(foreign_keys=[tenant_id])
    trusted_tenant: Mapped[Tenant] = relationship(foreign_keys=[trusted_tenant_id])

    def __repr__(self) -> str:
        return f"<TenantTrustedSource tenant={self.tenant_id} trusted={self.trusted_tenant_id}>"

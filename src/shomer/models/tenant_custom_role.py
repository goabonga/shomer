# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""TenantCustomRole model for tenant-specific RBAC roles."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from shomer.models.tenant import Tenant

from shomer.core.database import Base, TimestampMixin, UUIDMixin


class TenantCustomRole(Base, UUIDMixin, TimestampMixin):
    """Tenant-specific custom role beyond system-level roles.

    Allows each tenant to define their own roles with custom
    permissions, independent of the global RBAC roles.

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    tenant_id : uuid.UUID
        Foreign key to the tenant.
    name : str
        Role name, unique within the tenant.
    permissions : list[str]
        Permission strings granted by this role.
    tenant : Tenant
        The tenant that owns this role.
    created_at : datetime
        Row creation timestamp (from TimestampMixin).
    updated_at : datetime
        Last update timestamp (from TimestampMixin).
    """

    __tablename__ = "tenant_custom_roles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_tenant_role_name"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    permissions: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    # Relationships
    tenant: Mapped[Tenant] = relationship()

    def __repr__(self) -> str:
        return f"<TenantCustomRole tenant={self.tenant_id} name={self.name}>"

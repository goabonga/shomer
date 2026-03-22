# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""TenantMember model for multi-tenancy membership."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from shomer.models.tenant import Tenant
    from shomer.models.user import User

from shomer.core.database import Base, TimestampMixin, UUIDMixin


class TenantMember(Base, UUIDMixin, TimestampMixin):
    """Membership linking a user to a tenant with a role.

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    user_id : uuid.UUID
        Foreign key to the user.
    tenant_id : uuid.UUID
        Foreign key to the tenant.
    role : str
        Member role within the tenant (e.g. ``owner``, ``admin``, ``member``).
    joined_at : datetime
        When the user joined the tenant.
    user : User
        The member user.
    tenant : Tenant
        The tenant.
    created_at : datetime
        Row creation timestamp (from TimestampMixin).
    updated_at : datetime
        Last update timestamp (from TimestampMixin).
    """

    __tablename__ = "tenant_members"
    __table_args__ = (
        UniqueConstraint("user_id", "tenant_id", name="uq_tenant_member"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="member",
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Relationships
    user: Mapped[User] = relationship()
    tenant: Mapped[Tenant] = relationship()

    def __repr__(self) -> str:
        return f"<TenantMember user={self.user_id} tenant={self.tenant_id} role={self.role}>"

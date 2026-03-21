# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""UserRole model for assigning roles to users within tenants."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from shomer.models.role import Role
    from shomer.models.user import User

from shomer.core.database import Base, TimestampMixin, UUIDMixin


class UserRole(Base, UUIDMixin, TimestampMixin):
    """Assignment of a role to a user, optionally scoped to a tenant.

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    user_id : uuid.UUID
        Foreign key to the user.
    role_id : uuid.UUID
        Foreign key to the role.
    tenant_id : uuid.UUID or None
        Optional tenant scope. ``None`` means global assignment.
    expires_at : datetime or None
        Optional expiration for temporary role assignments.
    user : User
        The associated user.
    role : Role
        The associated role.
    created_at : datetime
        Row creation timestamp (from TimestampMixin).
    updated_at : datetime
        Last update timestamp (from TimestampMixin).
    """

    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", "tenant_id", name="uq_user_role_tenant"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        nullable=True,
        index=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user: Mapped[User] = relationship()
    role: Mapped[Role] = relationship()

    def __repr__(self) -> str:
        return f"<UserRole user={self.user_id} role={self.role_id} tenant={self.tenant_id}>"

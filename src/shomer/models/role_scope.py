# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""RoleScope junction table for many-to-many Role ↔ Scope."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from shomer.core.database import Base, TimestampMixin, UUIDMixin


class RoleScope(Base, UUIDMixin, TimestampMixin):
    """Many-to-many association between Role and Scope.

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    role_id : uuid.UUID
        Foreign key to the role.
    scope_id : uuid.UUID
        Foreign key to the scope.
    created_at : datetime
        Row creation timestamp (from TimestampMixin).
    updated_at : datetime
        Last update timestamp (from TimestampMixin).
    """

    __tablename__ = "role_scopes"
    __table_args__ = (UniqueConstraint("role_id", "scope_id", name="uq_role_scope"),)

    role_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scope_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("scopes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return f"<RoleScope role={self.role_id} scope={self.scope_id}>"

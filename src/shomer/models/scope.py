# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Scope model for RBAC authorization."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from shomer.models.role import Role

from shomer.core.database import Base, TimestampMixin, UUIDMixin


class Scope(Base, UUIDMixin, TimestampMixin):
    """Authorization scope (permission).

    Scopes use dot/colon notation to represent hierarchical permissions
    (e.g. ``admin:users:read``, ``api:orders:write``).

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    name : str
        Unique scope name (e.g. ``admin:users:read``).
    description : str or None
        Human-readable description of the scope.
    roles : list[Role]
        Roles that include this scope (via RoleScope).
    created_at : datetime
        Row creation timestamp (from TimestampMixin).
    updated_at : datetime
        Last update timestamp (from TimestampMixin).
    """

    __tablename__ = "scopes"

    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    roles: Mapped[list[Role]] = relationship(
        secondary="role_scopes",
        back_populates="scopes",
        viewonly=True,
    )

    def __repr__(self) -> str:
        return f"<Scope name={self.name}>"

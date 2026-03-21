# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Role model for RBAC authorization."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from shomer.models.scope import Scope

from shomer.core.database import Base, TimestampMixin, UUIDMixin


class Role(Base, UUIDMixin, TimestampMixin):
    """Authorization role.

    Roles group scopes together. System roles (``is_system=True``)
    cannot be deleted by users.

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    name : str
        Unique role name (e.g. ``admin``, ``editor``).
    description : str or None
        Human-readable description.
    is_system : bool
        Whether this is a built-in system role.
    scopes : list[Scope]
        Scopes assigned to this role (via RoleScope).
    created_at : datetime
        Row creation timestamp (from TimestampMixin).
    updated_at : datetime
        Last update timestamp (from TimestampMixin).
    """

    __tablename__ = "roles"

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
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    scopes: Mapped[list[Scope]] = relationship(
        secondary="role_scopes",
        back_populates="roles",
        viewonly=True,
    )

    def __repr__(self) -> str:
        return f"<Role name={self.name} system={self.is_system}>"

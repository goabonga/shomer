# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""UserPassword model."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from shomer.core.database import Base, TimestampMixin, UUIDMixin


class UserPassword(Base, UUIDMixin, TimestampMixin):
    """User password hash with history tracking.

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    user_id : uuid.UUID
        Foreign key to the users table.
    password_hash : str
        Argon2id hashed password.
    is_current : bool
        Whether this is the active password (``False`` for history).
    """

    __tablename__ = "user_passwords"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    is_current: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<UserPassword user_id={self.user_id} current={self.is_current}>"

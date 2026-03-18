# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""PasswordResetToken model for password reset flows."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from shomer.models.user import User

from shomer.core.database import Base, TimestampMixin, UUIDMixin


class PasswordResetToken(Base, UUIDMixin, TimestampMixin):
    """Password reset token with expiration and single-use flag.

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    token : uuid.UUID
        Unique token sent to the user (distinct from the PK).
    user_id : uuid.UUID
        Foreign key to the users table.
    expires_at : datetime
        Expiration timestamp.
    used : bool
        Whether the token has already been consumed.
    created_at : datetime
        Row creation timestamp (from TimestampMixin).
    updated_at : datetime
        Last update timestamp (from TimestampMixin).
    """

    __tablename__ = "password_reset_tokens"

    token: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    used: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    user: Mapped[User] = relationship(back_populates="password_reset_tokens")

    def __repr__(self) -> str:
        return f"<PasswordResetToken user_id={self.user_id} used={self.used}>"

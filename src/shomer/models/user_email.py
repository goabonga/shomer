# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""UserEmail model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from shomer.core.database import Base, TimestampMixin, UUIDMixin


class UserEmail(Base, UUIDMixin, TimestampMixin):
    """User email address with verification and primary flag.

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    user_id : uuid.UUID
        Foreign key to the users table.
    email : str
        Email address (unique across the system).
    is_verified : bool
        Whether the email has been verified.
    is_primary : bool
        Whether this is the user's primary email.
    verified_at : datetime or None
        Timestamp when the email was verified.
    """

    __tablename__ = "user_emails"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<UserEmail email={self.email} verified={self.is_verified}>"

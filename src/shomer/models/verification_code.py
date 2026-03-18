# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""VerificationCode model for email verification."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from shomer.core.database import Base, TimestampMixin, UUIDMixin


class VerificationCode(Base, UUIDMixin, TimestampMixin):
    """Email verification code with expiration and single-use flag.

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    email : str
        Email address this code was sent to.
    code : str
        Six-digit verification code.
    expires_at : datetime
        Expiration timestamp.
    used : bool
        Whether the code has already been consumed.
    created_at : datetime
        Row creation timestamp (from TimestampMixin).
    updated_at : datetime
        Last update timestamp (from TimestampMixin).
    """

    __tablename__ = "verification_codes"

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(
        String(6),
        nullable=False,
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

    def __repr__(self) -> str:
        return f"<VerificationCode email={self.email} used={self.used}>"

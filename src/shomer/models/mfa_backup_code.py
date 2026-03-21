# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""MFABackupCode model for single-use recovery codes."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from shomer.models.user_mfa import UserMFA

from shomer.core.database import Base, TimestampMixin, UUIDMixin


class MFABackupCode(Base, UUIDMixin, TimestampMixin):
    """Single-use MFA backup (recovery) code.

    Backup codes are hashed with Argon2id before storage.
    Each code can only be used once.

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    user_mfa_id : uuid.UUID
        Foreign key to the UserMFA record.
    code_hash : str
        Argon2id hash of the backup code.
    is_used : bool
        Whether this code has been consumed.
    user_mfa : UserMFA
        The associated MFA configuration.
    created_at : datetime
        Row creation timestamp (from TimestampMixin).
    updated_at : datetime
        Last update timestamp (from TimestampMixin).
    """

    __tablename__ = "mfa_backup_codes"

    user_mfa_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user_mfa.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    is_used: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    user_mfa: Mapped[UserMFA] = relationship(back_populates="backup_codes")

    def __repr__(self) -> str:
        return f"<MFABackupCode id={self.id} used={self.is_used}>"

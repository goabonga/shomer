# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""UserMFA model for multi-factor authentication."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from shomer.models.mfa_backup_code import MFABackupCode
    from shomer.models.user import User

from shomer.core.database import Base, TimestampMixin, UUIDMixin


class UserMFA(Base, UUIDMixin, TimestampMixin):
    """MFA configuration for a user.

    Stores the encrypted TOTP secret, enabled state, and list of
    active MFA methods (totp, email, backup).

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    user_id : uuid.UUID
        Foreign key to the user.
    totp_secret_encrypted : str or None
        AES-256-GCM encrypted TOTP secret (base32-encoded before encryption).
    is_enabled : bool
        Whether MFA is active for this user.
    methods : list[str]
        Active MFA methods (e.g. ``["totp", "email", "backup"]``).
    user : User
        The associated user.
    backup_codes : list[MFABackupCode]
        Associated backup codes.
    created_at : datetime
        Row creation timestamp (from TimestampMixin).
    updated_at : datetime
        Last update timestamp (from TimestampMixin).
    """

    __tablename__ = "user_mfa"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    totp_secret_encrypted: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    methods: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    # Relationships
    user: Mapped[User] = relationship(back_populates="mfa")
    backup_codes: Mapped[list[MFABackupCode]] = relationship(
        back_populates="user_mfa",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<UserMFA user_id={self.user_id} enabled={self.is_enabled}>"

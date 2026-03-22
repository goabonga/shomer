# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""PersonalAccessToken model for API key authentication."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from shomer.models.user import User

from shomer.core.database import Base, TimestampMixin, UUIDMixin

#: Token prefix for easy identification in logs and revocation.
PAT_PREFIX = "shm_pat_"


class PersonalAccessToken(Base, UUIDMixin, TimestampMixin):
    """Personal Access Token for programmatic API access.

    Tokens are prefixed with ``shm_pat_`` for easy identification.
    Only the hash of the token value is stored; the raw token is
    shown once at creation time.

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    user_id : uuid.UUID
        Foreign key to the token owner.
    name : str
        Human-readable label (e.g. ``"CI deploy key"``).
    token_prefix : str
        First 8 characters of the token (``shm_pat_...``) for display.
    token_hash : str
        SHA-256 hash of the full token for lookup and verification.
    scopes : str
        Space-separated scopes granted to this token.
    expires_at : datetime or None
        Optional expiration. ``None`` means non-expiring.
    last_used_at : datetime or None
        Timestamp of the last API call using this token.
    is_revoked : bool
        Whether the token has been revoked.
    user : User
        The token owner.
    created_at : datetime
        Row creation timestamp (from TimestampMixin).
    updated_at : datetime
        Last update timestamp (from TimestampMixin).
    """

    __tablename__ = "personal_access_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    token_prefix: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )
    scopes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    user: Mapped[User] = relationship()

    def __repr__(self) -> str:
        return f"<PersonalAccessToken name={self.name} prefix={self.token_prefix}>"

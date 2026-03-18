# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""RefreshToken model with rotation chain and reuse detection."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from shomer.models.user import User

from shomer.core.database import Base, TimestampMixin, UUIDMixin


class RefreshToken(Base, UUIDMixin, TimestampMixin):
    """Persisted refresh token with rotation tracking.

    The ``family_id`` groups all tokens in a rotation chain.
    When a token is rotated, ``replaced_by`` points to the new token's ID.
    If a revoked token's ``family_id`` is reused, the entire family
    should be revoked (reuse detection).

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    token_hash : str
        Hashed refresh token value.
    family_id : uuid.UUID
        Rotation family identifier for reuse detection.
    user_id : uuid.UUID
        Foreign key to the users table.
    client_id : str
        OAuth2 client that requested the token.
    scopes : str
        Space-separated list of granted scopes.
    expires_at : datetime
        Token expiration timestamp.
    revoked : bool
        Whether the token has been revoked.
    replaced_by : uuid.UUID or None
        ID of the token that replaced this one on rotation.
    created_at : datetime
        Row creation timestamp (from TimestampMixin).
    updated_at : datetime
        Last update timestamp (from TimestampMixin).
    """

    __tablename__ = "refresh_tokens"

    token_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    family_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    client_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    scopes: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    replaced_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        nullable=True,
    )

    # Relationships
    user: Mapped[User] = relationship(back_populates="refresh_tokens")

    def __repr__(self) -> str:
        return f"<RefreshToken family={self.family_id} revoked={self.revoked}>"

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""AccessToken model for token storage and revocation.

user_id is nullable to support client_credentials grants (M2M tokens
that are not associated with any user).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from shomer.models.user import User

from shomer.core.database import Base, TimestampMixin, UUIDMixin


class AccessToken(Base, UUIDMixin, TimestampMixin):
    """Persisted access token for lookup and revocation.

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    jti : str
        JWT ID (unique token identifier, indexed).
    user_id : uuid.UUID or None
        Foreign key to the users table (None for client_credentials grants).
    client_id : str
        OAuth2 client that requested the token.
    scopes : str
        Space-separated list of granted scopes.
    expires_at : datetime
        Token expiration timestamp.
    revoked : bool
        Whether the token has been revoked.
    created_at : datetime
        Row creation timestamp (from TimestampMixin).
    updated_at : datetime
        Last update timestamp (from TimestampMixin).
    """

    __tablename__ = "access_tokens"

    jti: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
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

    # Relationships
    user: Mapped[User | None] = relationship(back_populates="access_tokens")

    def __repr__(self) -> str:
        return f"<AccessToken jti={self.jti} revoked={self.revoked}>"

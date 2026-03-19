# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""AuthorizationCode model for RFC 6749 authorization code grant."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from shomer.models.user import User

from shomer.core.database import Base, TimestampMixin, UUIDMixin


class AuthorizationCode(Base, UUIDMixin, TimestampMixin):
    """Authorization code bridging /authorize and /token.

    Short-lived, single-use code with optional PKCE support
    per RFC 6749 §4.1 and RFC 7636.

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    code : str
        The authorization code value (unique, indexed).
    user_id : uuid.UUID
        Foreign key to the users table.
    client_id : str
        OAuth2 client identifier (not a FK — matches OAuth2Client.client_id).
    redirect_uri : str
        The redirect URI used in the authorization request.
    scopes : str
        Space-separated list of granted scopes.
    nonce : str or None
        OIDC nonce for ID token binding.
    code_challenge : str or None
        PKCE code challenge (RFC 7636).
    code_challenge_method : str or None
        PKCE challenge method (``plain`` or ``S256``).
    expires_at : datetime
        Expiration timestamp (default 10 minutes).
    used_at : datetime or None
        Timestamp when the code was exchanged (single-use enforcement).
    is_used : bool
        Whether the code has been consumed.
    created_at : datetime
        Row creation timestamp (from TimestampMixin).
    updated_at : datetime
        Last update timestamp (from TimestampMixin).
    """

    __tablename__ = "authorization_codes"

    code: Mapped[str] = mapped_column(
        String(255),
        unique=True,
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
        index=True,
    )
    redirect_uri: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    scopes: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )
    nonce: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # PKCE (RFC 7636)
    code_challenge: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )
    code_challenge_method: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    is_used: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    user: Mapped[User] = relationship()

    def __repr__(self) -> str:
        return f"<AuthorizationCode code={self.code[:8]}... client={self.client_id}>"

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""User model."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from shomer.models.access_token import AccessToken
    from shomer.models.password_reset_token import PasswordResetToken
    from shomer.models.refresh_token import RefreshToken
    from shomer.models.session import Session
    from shomer.models.user_email import UserEmail
    from shomer.models.user_mfa import UserMFA
    from shomer.models.user_password import UserPassword
    from shomer.models.user_profile import UserProfile

from shomer.core.database import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    """User account.

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    username : str or None
        Optional display name.
    is_active : bool
        Whether the account is active.
    registration_tenant_id : uuid.UUID or None
        The tenant where the user originally registered.
    created_at : datetime
        Row creation timestamp (from TimestampMixin).
    updated_at : datetime
        Last update timestamp (from TimestampMixin).
    profile : UserProfile or None
        One-to-one OIDC profile (lazy-loaded).
    mfa : UserMFA or None
        One-to-one MFA configuration (lazy-loaded).
    """

    __tablename__ = "users"

    username: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    registration_tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    emails: Mapped[list[UserEmail]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    passwords: Mapped[list[UserPassword]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    profile: Mapped[UserProfile | None] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    sessions: Mapped[list[Session]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    password_reset_tokens: Mapped[list[PasswordResetToken]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    access_tokens: Mapped[list[AccessToken]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    mfa: Mapped[UserMFA | None] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} active={self.is_active}>"

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""UserProfile model for OIDC standard claims."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shomer.core.database import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from shomer.models.user import User


class UserProfile(Base, UUIDMixin, TimestampMixin):
    """User profile storing standard OIDC claims.

    See `OpenID Connect Core 1.0 §5.1
    <https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims>`_.

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    user_id : uuid.UUID
        Foreign key to the users table (unique, one-to-one).
    name : str or None
        Full name.
    given_name : str or None
        First name.
    family_name : str or None
        Last name.
    middle_name : str or None
        Middle name.
    nickname : str or None
        Casual name.
    preferred_username : str or None
        Preferred username.
    profile_url : str or None
        Profile page URL.
    picture_url : str or None
        Profile picture URL.
    website : str or None
        Personal website URL.
    gender : str or None
        Gender.
    birthdate : str or None
        Birthday in YYYY-MM-DD format.
    zoneinfo : str or None
        Time zone (e.g. ``Europe/Paris``).
    locale : str or None
        Locale (e.g. ``en-US``).
    address_formatted : str or None
        Full mailing address, formatted.
    address_street : str or None
        Street address.
    address_locality : str or None
        City or locality.
    address_region : str or None
        State, province or region.
    address_postal_code : str or None
        Postal / ZIP code.
    address_country : str or None
        Country.
    phone_number : str or None
        Phone number.
    phone_number_verified : bool
        Whether the phone number has been verified.
    """

    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Standard OIDC profile claims
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    given_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    family_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    middle_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nickname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    preferred_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    profile_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    picture_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    website: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(50), nullable=True)
    birthdate: Mapped[str | None] = mapped_column(String(10), nullable=True)
    zoneinfo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    locale: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Address claims
    address_formatted: Mapped[str | None] = mapped_column(Text, nullable=True)
    address_street: Mapped[str | None] = mapped_column(String(500), nullable=True)
    address_locality: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_region: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_postal_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address_country: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Phone claims
    phone_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    phone_number_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Relationships
    user: Mapped[User] = relationship(back_populates="profile")

    def __repr__(self) -> str:
        return f"<UserProfile user_id={self.user_id} name={self.name}>"

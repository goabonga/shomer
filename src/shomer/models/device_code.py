# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""DeviceCode model for RFC 8628 device authorization grant."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from shomer.models.user import User

from shomer.core.database import Base, TimestampMixin, UUIDMixin


class DeviceCodeStatus(str, enum.Enum):
    """Status of a device authorization request.

    Attributes
    ----------
    PENDING
        Waiting for user to authorize.
    APPROVED
        User approved the request.
    DENIED
        User denied the request.
    EXPIRED
        Request expired before user acted.
    """

    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"


class DeviceCode(Base, UUIDMixin, TimestampMixin):
    """Device authorization request per RFC 8628.

    Stores the device_code (for polling), user_code (for user entry),
    and tracks the lifecycle from pending through approval/denial/expiry.

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    device_code : str
        Unique device code for client polling (indexed).
    user_code : str
        Human-friendly code for user entry (e.g. ``ABCD-EFGH``).
    client_id : str
        OAuth2 client that initiated the request.
    scopes : str
        Space-separated list of requested scopes.
    verification_uri : str
        URI where the user should enter the user_code.
    verification_uri_complete : str or None
        Full URI with user_code pre-filled.
    interval : int
        Minimum polling interval in seconds (default 5).
    status : DeviceCodeStatus
        Current status of the request.
    user_id : uuid.UUID or None
        Foreign key to users table (set when user approves).
    expires_at : datetime
        Expiration timestamp (default 15 minutes).
    created_at : datetime
        Row creation timestamp (from TimestampMixin).
    updated_at : datetime
        Last update timestamp (from TimestampMixin).
    """

    __tablename__ = "device_codes"

    device_code: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    user_code: Mapped[str] = mapped_column(
        String(16),
        unique=True,
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
    verification_uri: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )
    verification_uri_complete: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )
    interval: Mapped[int] = mapped_column(
        Integer,
        default=5,
        nullable=False,
    )
    status: Mapped[DeviceCodeStatus] = mapped_column(
        Enum(DeviceCodeStatus, name="device_code_status", native_enum=False),
        default=DeviceCodeStatus.PENDING,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Relationships
    user: Mapped[User | None] = relationship()

    def __repr__(self) -> str:
        return f"<DeviceCode user_code={self.user_code} status={self.status.value}>"

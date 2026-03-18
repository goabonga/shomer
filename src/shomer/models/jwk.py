# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""JWK model with encrypted private key storage."""

from __future__ import annotations

import enum

from sqlalchemy import Enum, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shomer.core.database import Base, TimestampMixin, UUIDMixin


class JWKStatus(str, enum.Enum):
    """Lifecycle status of a JSON Web Key.

    Attributes
    ----------
    ACTIVE
        Key is in use for signing.
    ROTATED
        Key has been replaced but can still verify old tokens.
    REVOKED
        Key is permanently disabled.
    """

    ACTIVE = "active"
    ROTATED = "rotated"
    REVOKED = "revoked"


class JWK(Base, UUIDMixin, TimestampMixin):
    """JSON Web Key with AES-256-GCM encrypted private key.

    The private key is stored as AES-256-GCM ciphertext (nonce + ciphertext).
    The public key is stored as a JWK JSON string in clear text.

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    kid : str
        Key ID (unique, indexed).
    algorithm : str
        JWA algorithm identifier (e.g. ``RS256``).
    public_key : str
        Public key in JWK JSON format.
    private_key_enc : bytes
        AES-256-GCM encrypted private key material.
    status : JWKStatus
        Key lifecycle status.
    created_at : datetime
        Row creation timestamp (from TimestampMixin).
    updated_at : datetime
        Last update timestamp (from TimestampMixin).
    """

    __tablename__ = "jwks"

    kid: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    algorithm: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    public_key: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    private_key_enc: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
    )
    status: Mapped[JWKStatus] = mapped_column(
        Enum(JWKStatus, name="jwk_status", native_enum=False),
        default=JWKStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return f"<JWK kid={self.kid} alg={self.algorithm} status={self.status.value}>"

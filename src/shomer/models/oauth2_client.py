# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""OAuth2Client model for RFC 6749 client registration."""

from __future__ import annotations

import enum

from sqlalchemy import Boolean, Enum, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from shomer.core.database import Base, TimestampMixin, UUIDMixin


class ClientType(str, enum.Enum):
    """OAuth2 client type per RFC 6749 §2.1.

    Attributes
    ----------
    CONFIDENTIAL
        Client capable of maintaining the confidentiality of its credentials.
    PUBLIC
        Client incapable of maintaining the confidentiality of its credentials.
    """

    CONFIDENTIAL = "confidential"
    PUBLIC = "public"


class OAuth2Client(Base, UUIDMixin, TimestampMixin):
    """OAuth2 client entity.

    Stores client credentials, allowed grant types, redirect URIs,
    and OIDC metadata per RFC 6749 and OpenID Connect Dynamic Registration.

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    client_id : str
        Unique client identifier (indexed).
    client_secret_hash : str or None
        Hashed client secret (None for public clients).
    client_name : str
        Human-readable client name.
    client_type : ClientType
        Confidential or public.
    redirect_uris : list
        Allowed redirect URIs (JSON array).
    grant_types : list
        Allowed grant types (JSON array).
    response_types : list
        Allowed response types (JSON array).
    scopes : list
        Allowed scopes (JSON array).
    logo_uri : str or None
        URL of the client logo.
    tos_uri : str or None
        URL of the Terms of Service.
    policy_uri : str or None
        URL of the privacy policy.
    contacts : list
        Contact email addresses (JSON array).
    is_active : bool
        Whether the client is active.
    created_at : datetime
        Row creation timestamp (from TimestampMixin).
    updated_at : datetime
        Last update timestamp (from TimestampMixin).
    """

    __tablename__ = "oauth2_clients"

    client_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    client_secret_hash: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    client_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    client_type: Mapped[ClientType] = mapped_column(
        Enum(ClientType, name="client_type", native_enum=False),
        default=ClientType.CONFIDENTIAL,
        nullable=False,
    )
    redirect_uris: Mapped[list[str]] = mapped_column(
        JSONB().with_variant(Text, "sqlite"),
        default=list,
        nullable=False,
    )
    grant_types: Mapped[list[str]] = mapped_column(
        JSONB().with_variant(Text, "sqlite"),
        default=list,
        nullable=False,
    )
    response_types: Mapped[list[str]] = mapped_column(
        JSONB().with_variant(Text, "sqlite"),
        default=list,
        nullable=False,
    )
    scopes: Mapped[list[str]] = mapped_column(
        JSONB().with_variant(Text, "sqlite"),
        default=list,
        nullable=False,
    )

    # OIDC metadata
    logo_uri: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )
    tos_uri: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )
    policy_uri: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )
    contacts: Mapped[list[str]] = mapped_column(
        JSONB().with_variant(Text, "sqlite"),
        default=list,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<OAuth2Client client_id={self.client_id} type={self.client_type.value}>"
        )

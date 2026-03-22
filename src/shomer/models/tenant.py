# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Tenant model for multi-tenancy."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from shomer.models.identity_provider import IdentityProvider
    from shomer.models.tenant_trusted_source import TenantTrustedSource

from shomer.core.database import Base, TimestampMixin, UUIDMixin


class TenantTrustMode(str, enum.Enum):
    """Trust mode for external user access.

    Defines how a tenant handles users from other tenants.

    Attributes
    ----------
    NONE
        Only users registered on this tenant can login.
    ALL
        Any authenticated user can login (open access).
    MEMBERS_ONLY
        Only explicit tenant members can login.
    SPECIFIC
        Only users from specific trusted tenants can login.
    """

    NONE = "none"
    ALL = "all"
    MEMBERS_ONLY = "members_only"
    SPECIFIC = "specific"


class Tenant(Base, UUIDMixin, TimestampMixin):
    """Organisation / workspace tenant.

    Each tenant has a unique slug used in URLs and an optional
    custom domain for white-label deployments.

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    slug : str
        Unique URL-safe identifier (e.g. ``acme-corp``).
    name : str
        Internal name.
    display_name : str
        Human-readable display name shown in UI.
    custom_domain : str or None
        Optional custom domain (e.g. ``auth.acme.com``).
    is_active : bool
        Whether the tenant is active.
    is_platform : bool
        Whether this is the platform (root) tenant.
    trust_mode : TenantTrustMode
        How this tenant handles external user access.
    settings : dict
        Tenant-specific configuration (branding, features, etc.).
    created_at : datetime
        Row creation timestamp (from TimestampMixin).
    updated_at : datetime
        Last update timestamp (from TimestampMixin).
    """

    __tablename__ = "tenants"

    slug: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    display_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="",
    )
    custom_domain: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_platform: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    trust_mode: Mapped[TenantTrustMode] = mapped_column(
        Enum(TenantTrustMode, name="tenant_trust_mode", native_enum=False),
        default=TenantTrustMode.NONE,
        nullable=False,
    )
    settings: Mapped[dict] = mapped_column(  # type: ignore[type-arg]
        JSON,
        default=dict,
        nullable=False,
    )

    # Relationships
    trusted_sources: Mapped[list[TenantTrustedSource]] = relationship(
        foreign_keys="TenantTrustedSource.tenant_id",
        cascade="all, delete-orphan",
    )
    identity_providers: Mapped[list[IdentityProvider]] = relationship(
        back_populates="tenant",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Tenant slug={self.slug} name={self.name}>"

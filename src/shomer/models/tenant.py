# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Tenant model for multi-tenancy."""

from __future__ import annotations

from sqlalchemy import JSON, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from shomer.core.database import Base, TimestampMixin, UUIDMixin


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
        Human-readable display name.
    custom_domain : str or None
        Optional custom domain (e.g. ``auth.acme.com``).
    is_active : bool
        Whether the tenant is active.
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
    settings: Mapped[dict] = mapped_column(  # type: ignore[type-arg]
        JSON,
        default=dict,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Tenant slug={self.slug} name={self.name}>"

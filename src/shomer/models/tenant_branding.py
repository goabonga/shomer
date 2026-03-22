# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""TenantBranding model for tenant visual customization."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from shomer.models.tenant import Tenant

from shomer.core.database import Base, TimestampMixin, UUIDMixin


class TenantBranding(Base, UUIDMixin, TimestampMixin):
    """Visual branding configuration for a tenant.

    Controls the look and feel of auth pages (login, consent, error)
    and emails for the tenant. All color fields accept CSS hex values.

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    tenant_id : uuid.UUID
        Foreign key to the tenant (one-to-one).
    logo_url : str or None
        URL to the tenant's logo image.
    logo_dark_url : str or None
        URL to the logo variant for dark backgrounds.
    favicon_url : str or None
        URL to the tenant's favicon.
    primary_color : str or None
        Primary brand color (hex).
    secondary_color : str or None
        Secondary brand color (hex).
    accent_color : str or None
        Accent/highlight color (hex).
    background_color : str or None
        Page background color (hex).
    surface_color : str or None
        Card/surface background color (hex).
    text_color : str or None
        Primary text color (hex).
    text_muted_color : str or None
        Muted/secondary text color (hex).
    error_color : str or None
        Error state color (hex).
    success_color : str or None
        Success state color (hex).
    border_color : str or None
        Border color (hex).
    warning_color : str or None
        Warning state color (hex).
    info_color : str or None
        Informational state color (hex).
    font_family : str or None
        CSS font-family value.
    font_url : str or None
        URL to import custom font (e.g. Google Fonts).
    custom_css : str or None
        Raw CSS injected into auth pages.
    custom_js : str or None
        Raw JavaScript injected into auth pages.
    show_powered_by : bool
        Whether to display "Powered by Shomer" footer.
    tenant : Tenant
        The associated tenant.
    created_at : datetime
        Row creation timestamp (from TimestampMixin).
    updated_at : datetime
        Last update timestamp (from TimestampMixin).
    """

    __tablename__ = "tenant_brandings"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # Logo and favicon
    logo_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    logo_dark_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    favicon_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # Colors
    primary_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    secondary_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    accent_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    background_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    surface_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    text_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    text_muted_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    error_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    success_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    border_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    warning_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    info_color: Mapped[str | None] = mapped_column(String(7), nullable=True)

    # Typography
    font_family: Mapped[str | None] = mapped_column(String(500), nullable=True)
    font_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # Custom code
    custom_css: Mapped[str | None] = mapped_column(Text, nullable=True)
    custom_js: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Settings
    show_powered_by: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    tenant: Mapped[Tenant] = relationship()

    def __repr__(self) -> str:
        return f"<TenantBranding tenant_id={self.tenant_id}>"

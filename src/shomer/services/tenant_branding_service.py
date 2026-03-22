# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Tenant branding resolution and template management service.

Resolves branding from the database, generates CSS variables,
manages custom template CRUD, and provides a DB-first template
loader with filesystem fallback.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shomer.models.tenant_branding import TenantBranding
from shomer.models.tenant_template import TenantTemplate


@dataclass
class BrandingContext:
    """Resolved branding context for template rendering.

    All color fields default to a dark-theme palette matching the
    admin UI. Override per-tenant via :class:`TenantBranding`.

    Attributes
    ----------
    tenant_id : uuid.UUID or None
        Tenant ID (None for default).
    tenant_slug : str
        Tenant slug for display.
    display_name : str
        Tenant display name.
    logo_url : str or None
        Logo URL.
    logo_dark_url : str or None
        Logo URL for dark backgrounds.
    favicon_url : str or None
        Favicon URL.
    primary_color : str
        Primary brand color.
    secondary_color : str
        Secondary brand color.
    accent_color : str
        Accent/highlight color.
    background_color : str
        Page background color.
    surface_color : str
        Card/surface background color.
    text_color : str
        Primary text color.
    text_muted_color : str
        Muted text color.
    error_color : str
        Error state color.
    success_color : str
        Success state color.
    border_color : str
        Border color.
    warning_color : str
        Warning state color.
    info_color : str
        Info state color.
    font_family : str
        CSS font-family.
    font_url : str or None
        URL to import custom font.
    custom_css : str
        Raw CSS to inject.
    custom_js : str
        Raw JS to inject.
    show_powered_by : bool
        Whether to show "Powered by Shomer".
    """

    tenant_id: uuid.UUID | None = None
    tenant_slug: str = ""
    display_name: str = ""

    logo_url: str | None = None
    logo_dark_url: str | None = None
    favicon_url: str | None = None

    primary_color: str = "#e94560"
    secondary_color: str = "#0f3460"
    accent_color: str = "#e94560"
    background_color: str = "#1a1a2e"
    surface_color: str = "#16213e"
    text_color: str = "#e0e0e0"
    text_muted_color: str = "#a0a0a0"
    error_color: str = "#ff6b6b"
    success_color: str = "#00b894"
    border_color: str = "#0f3460"
    warning_color: str = "#fdcb6e"
    info_color: str = "#74b9ff"

    font_family: str = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif"
    font_url: str | None = None

    custom_css: str = ""
    custom_js: str = ""
    show_powered_by: bool = True

    def to_css_variables(self) -> str:
        """Generate CSS custom properties from branding config.

        Returns
        -------
        str
            A ``:root`` block with CSS variables.
        """
        return (
            ":root {\n"
            f"    --primary-color: {self.primary_color};\n"
            f"    --secondary-color: {self.secondary_color};\n"
            f"    --accent-color: {self.accent_color};\n"
            f"    --background-color: {self.background_color};\n"
            f"    --surface-color: {self.surface_color};\n"
            f"    --text-color: {self.text_color};\n"
            f"    --text-muted-color: {self.text_muted_color};\n"
            f"    --error-color: {self.error_color};\n"
            f"    --success-color: {self.success_color};\n"
            f"    --border-color: {self.border_color};\n"
            f"    --warning-color: {self.warning_color};\n"
            f"    --info-color: {self.info_color};\n"
            f"    --font-family: {self.font_family};\n"
            "}"
        )

    def get_font_import(self) -> str:
        """Generate CSS font import if a custom font URL is set.

        Returns
        -------
        str
            ``@import url(...)`` or empty string.
        """
        if self.font_url:
            return f'@import url("{self.font_url}");'
        return ""


#: Default branding when no tenant or no custom branding is configured.
DEFAULT_BRANDING = BrandingContext()

#: Templates that can be customized per tenant.
CUSTOMIZABLE_TEMPLATES: list[str] = [
    "base.html",
    "auth/login.html",
    "auth/register.html",
    "auth/verify.html",
    "auth/change_password.html",
    "auth/forgot_password.html",
    "auth/reset_password.html",
    "mfa/setup.html",
    "mfa/challenge.html",
    "oauth2/consent.html",
    "oauth2/error.html",
    "device/verify.html",
    "email/verification.html",
    "email/password_reset.html",
    "email/mfa_code.html",
]


class TenantBrandingService:
    """Manage tenant branding and custom template overrides.

    Attributes
    ----------
    session : AsyncSession
        Database session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Branding resolution ───────────────────────────────────────────

    async def get_branding(self, tenant_id: uuid.UUID | None) -> BrandingContext:
        """Resolve the branding context for a tenant.

        Parameters
        ----------
        tenant_id : uuid.UUID or None
            The tenant ID. Returns default branding if None.

        Returns
        -------
        BrandingContext
            The resolved branding context.
        """
        if tenant_id is None:
            return DEFAULT_BRANDING

        stmt = select(TenantBranding).where(
            TenantBranding.tenant_id == tenant_id,
        )
        result = await self.session.execute(stmt)
        branding = result.scalar_one_or_none()

        if branding is None:
            return DEFAULT_BRANDING

        return BrandingContext(
            tenant_id=tenant_id,
            logo_url=branding.logo_url,
            logo_dark_url=branding.logo_dark_url,
            favicon_url=branding.favicon_url,
            primary_color=branding.primary_color or DEFAULT_BRANDING.primary_color,
            secondary_color=branding.secondary_color
            or DEFAULT_BRANDING.secondary_color,
            accent_color=branding.accent_color or DEFAULT_BRANDING.accent_color,
            background_color=branding.background_color
            or DEFAULT_BRANDING.background_color,
            surface_color=branding.surface_color or DEFAULT_BRANDING.surface_color,
            text_color=branding.text_color or DEFAULT_BRANDING.text_color,
            text_muted_color=branding.text_muted_color
            or DEFAULT_BRANDING.text_muted_color,
            error_color=branding.error_color or DEFAULT_BRANDING.error_color,
            success_color=branding.success_color or DEFAULT_BRANDING.success_color,
            border_color=branding.border_color or DEFAULT_BRANDING.border_color,
            warning_color=branding.warning_color or DEFAULT_BRANDING.warning_color,
            info_color=branding.info_color or DEFAULT_BRANDING.info_color,
            font_family=branding.font_family or DEFAULT_BRANDING.font_family,
            font_url=branding.font_url,
            custom_css=branding.custom_css or "",
            custom_js=branding.custom_js or "",
            show_powered_by=branding.show_powered_by,
        )

    async def get_branding_dict(self, tenant_id: uuid.UUID | None) -> dict[str, object]:
        """Get branding as a dict suitable for Jinja2 template context.

        Parameters
        ----------
        tenant_id : uuid.UUID or None
            The tenant ID.

        Returns
        -------
        dict[str, object]
            Branding variables including CSS variables and font import.
        """
        ctx = await self.get_branding(tenant_id)
        return {
            "branding": ctx,
            "branding_css_variables": ctx.to_css_variables(),
            "branding_font_import": ctx.get_font_import(),
        }

    # ── Branding CRUD ─────────────────────────────────────────────────

    async def save_branding(
        self, tenant_id: uuid.UUID, **kwargs: Any
    ) -> TenantBranding:
        """Create or update branding for a tenant.

        Parameters
        ----------
        tenant_id : uuid.UUID
            The tenant ID.
        **kwargs
            Branding fields to set.

        Returns
        -------
        TenantBranding
            The created or updated record.
        """
        stmt = select(TenantBranding).where(
            TenantBranding.tenant_id == tenant_id,
        )
        result = await self.session.execute(stmt)
        branding = result.scalar_one_or_none()

        if branding:
            for key, value in kwargs.items():
                if hasattr(branding, key):
                    setattr(branding, key, value)
            await self.session.flush()
            return branding

        branding = TenantBranding(tenant_id=tenant_id, **kwargs)
        self.session.add(branding)
        await self.session.flush()
        return branding

    async def delete_branding(self, tenant_id: uuid.UUID) -> bool:
        """Delete branding for a tenant (resets to defaults).

        Parameters
        ----------
        tenant_id : uuid.UUID
            The tenant ID.

        Returns
        -------
        bool
            True if deleted, False if not found.
        """
        stmt = select(TenantBranding).where(
            TenantBranding.tenant_id == tenant_id,
        )
        result = await self.session.execute(stmt)
        branding = result.scalar_one_or_none()
        if branding:
            await self.session.delete(branding)
            await self.session.flush()
            return True
        return False

    # ── Template resolution ───────────────────────────────────────────

    async def get_template(
        self,
        tenant_id: uuid.UUID | None,
        template_name: str,
    ) -> str | None:
        """Get a custom template for a tenant (active only).

        Parameters
        ----------
        tenant_id : uuid.UUID or None
            The tenant ID. Returns None if no tenant.
        template_name : str
            Template path (e.g. ``auth/login.html``).

        Returns
        -------
        str or None
            The custom template content, or None to use the default.
        """
        if tenant_id is None:
            return None

        stmt = select(TenantTemplate.content).where(
            TenantTemplate.tenant_id == tenant_id,
            TenantTemplate.template_name == template_name,
            TenantTemplate.is_active == True,  # noqa: E712
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_default_template_content(self, template_name: str) -> str | None:
        """Read the default template content from filesystem.

        Parameters
        ----------
        template_name : str
            Template path relative to the templates directory.

        Returns
        -------
        str or None
            Content of the default template, or None if not found.
        """
        from shomer.app import templates as tpl_engine

        template_path = Path(tpl_engine.env.loader.searchpath[0]) / template_name  # type: ignore[union-attr]
        if template_path.exists():
            return template_path.read_text(encoding="utf-8")
        return None

    # ── Template CRUD ─────────────────────────────────────────────────

    async def list_templates(self, tenant_id: uuid.UUID) -> list[TenantTemplate]:
        """List all custom templates for a tenant.

        Parameters
        ----------
        tenant_id : uuid.UUID
            The tenant ID.

        Returns
        -------
        list[TenantTemplate]
            All custom template records.
        """
        stmt = (
            select(TenantTemplate)
            .where(TenantTemplate.tenant_id == tenant_id)
            .order_by(TenantTemplate.template_name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def save_template(
        self,
        tenant_id: uuid.UUID,
        template_name: str,
        content: str,
        description: str | None = None,
        is_active: bool = True,
    ) -> TenantTemplate:
        """Create or update a custom template for a tenant.

        Parameters
        ----------
        tenant_id : uuid.UUID
            The tenant ID.
        template_name : str
            Template path.
        content : str
            Jinja2 template content.
        description : str or None
            Description of the customization.
        is_active : bool
            Whether the override is active.

        Returns
        -------
        TenantTemplate
            The created or updated record.
        """
        stmt = select(TenantTemplate).where(
            TenantTemplate.tenant_id == tenant_id,
            TenantTemplate.template_name == template_name,
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.content = content
            existing.description = description
            existing.is_active = is_active
            await self.session.flush()
            return existing

        template = TenantTemplate(
            tenant_id=tenant_id,
            template_name=template_name,
            content=content,
            description=description,
            is_active=is_active,
        )
        self.session.add(template)
        await self.session.flush()
        return template

    async def delete_template(self, tenant_id: uuid.UUID, template_name: str) -> bool:
        """Delete a custom template for a tenant.

        Parameters
        ----------
        tenant_id : uuid.UUID
            The tenant ID.
        template_name : str
            Template path to delete.

        Returns
        -------
        bool
            True if deleted, False if not found.
        """
        stmt = select(TenantTemplate).where(
            TenantTemplate.tenant_id == tenant_id,
            TenantTemplate.template_name == template_name,
        )
        result = await self.session.execute(stmt)
        template = result.scalar_one_or_none()
        if template:
            await self.session.delete(template)
            await self.session.flush()
            return True
        return False

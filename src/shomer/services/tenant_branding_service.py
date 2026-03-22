# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Tenant branding resolution service.

Resolves branding and custom templates for a tenant and provides
them as context variables for Jinja2 rendering.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shomer.models.tenant_branding import TenantBranding
from shomer.models.tenant_template import TenantTemplate


@dataclass
class BrandingContext:
    """Resolved branding context for template rendering.

    Attributes
    ----------
    logo_url : str or None
        Tenant logo URL.
    favicon_url : str or None
        Tenant favicon URL.
    primary_color : str
        Primary brand color (default ``#333333``).
    secondary_color : str
        Secondary brand color (default ``#666666``).
    custom_css : str
        Raw CSS to inject.
    """

    logo_url: str | None = None
    favicon_url: str | None = None
    primary_color: str = "#333333"
    secondary_color: str = "#666666"
    custom_css: str = ""


#: Default branding when no tenant or no custom branding is configured.
DEFAULT_BRANDING = BrandingContext()


class TenantBrandingService:
    """Resolve tenant branding and custom templates.

    Attributes
    ----------
    session : AsyncSession
        Database session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

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
            logo_url=branding.logo_url,
            favicon_url=branding.favicon_url,
            primary_color=branding.primary_color or DEFAULT_BRANDING.primary_color,
            secondary_color=branding.secondary_color
            or DEFAULT_BRANDING.secondary_color,
            custom_css=branding.custom_css or "",
        )

    async def get_template(
        self,
        tenant_id: uuid.UUID | None,
        template_type: str,
    ) -> str | None:
        """Get a custom template for a tenant.

        Parameters
        ----------
        tenant_id : uuid.UUID or None
            The tenant ID. Returns None if no tenant.
        template_type : str
            Template identifier (e.g. ``login``, ``consent``).

        Returns
        -------
        str or None
            The custom template content, or None to use the default.
        """
        if tenant_id is None:
            return None

        stmt = select(TenantTemplate.template_content).where(
            TenantTemplate.tenant_id == tenant_id,
            TenantTemplate.template_type == template_type,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_branding_dict(self, tenant_id: uuid.UUID | None) -> dict[str, object]:
        """Get branding as a dict suitable for Jinja2 template context.

        Parameters
        ----------
        tenant_id : uuid.UUID or None
            The tenant ID.

        Returns
        -------
        dict[str, object]
            Branding variables for template rendering.
        """
        ctx = await self.get_branding(tenant_id)
        return {
            "branding_logo_url": ctx.logo_url,
            "branding_favicon_url": ctx.favicon_url,
            "branding_primary_color": ctx.primary_color,
            "branding_secondary_color": ctx.secondary_color,
            "branding_custom_css": ctx.custom_css,
        }

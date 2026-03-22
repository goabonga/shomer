# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Tenant resolution service.

Resolves a tenant from a request using subdomain, path prefix,
or custom domain strategies.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from shomer.models.tenant import Tenant


class TenantResolverService:
    """Resolve the current tenant from HTTP request metadata.

    Strategies (tried in order):

    1. Subdomain — first label of the Host header
    2. Path prefix — ``/t/<slug>/...``
    3. Custom domain — full Host header lookup

    Attributes
    ----------
    session : AsyncSession
        Database session.
    """

    #: Hostnames that should never be treated as tenant subdomains.
    EXCLUDED_SUBDOMAINS: set[str] = {"www", "api", "app", "localhost", ""}

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def resolve(self, request: Request) -> uuid.UUID | None:
        """Resolve the tenant from the request.

        Parameters
        ----------
        request : Request
            The incoming HTTP request.

        Returns
        -------
        uuid.UUID or None
            The tenant ID, or None if no tenant matched.
        """
        # Strategy 1: subdomain
        tenant_id = await self._resolve_subdomain(request)
        if tenant_id is not None:
            return tenant_id

        # Strategy 2: path prefix /t/<slug>/...
        tenant_id = await self._resolve_path_prefix(request)
        if tenant_id is not None:
            return tenant_id

        # Strategy 3: custom domain
        tenant_id = await self._resolve_custom_domain(request)
        if tenant_id is not None:
            return tenant_id

        return None

    async def _resolve_subdomain(self, request: Request) -> uuid.UUID | None:
        """Resolve tenant from subdomain (e.g. acme.shomer.io → acme).

        Parameters
        ----------
        request : Request
            The incoming HTTP request.

        Returns
        -------
        uuid.UUID or None
            The tenant ID if found.
        """
        host = self._get_host(request)
        parts = host.split(".")
        if len(parts) < 3:
            return None

        subdomain = parts[0].lower()
        if subdomain in self.EXCLUDED_SUBDOMAINS:
            return None

        return await self._lookup_by_slug(subdomain)

    async def _resolve_path_prefix(self, request: Request) -> uuid.UUID | None:
        """Resolve tenant from path prefix (e.g. /t/acme/...).

        Parameters
        ----------
        request : Request
            The incoming HTTP request.

        Returns
        -------
        uuid.UUID or None
            The tenant ID if found.
        """
        path = request.url.path
        if not path.startswith("/t/"):
            return None

        # Extract slug from /t/<slug>/...
        segments = path.split("/")
        if len(segments) < 3 or not segments[2]:
            return None

        slug = segments[2].lower()
        return await self._lookup_by_slug(slug)

    async def _resolve_custom_domain(self, request: Request) -> uuid.UUID | None:
        """Resolve tenant from custom domain (e.g. auth.acme.com).

        Parameters
        ----------
        request : Request
            The incoming HTTP request.

        Returns
        -------
        uuid.UUID or None
            The tenant ID if found.
        """
        host = self._get_host(request)
        if not host:
            return None

        stmt = select(Tenant.id).where(
            Tenant.custom_domain == host,
            Tenant.is_active == True,  # noqa: E712
        )
        result = await self.session.execute(stmt)
        tenant_id = result.scalar_one_or_none()
        return tenant_id

    async def _lookup_by_slug(self, slug: str) -> uuid.UUID | None:
        """Look up an active tenant by slug.

        Parameters
        ----------
        slug : str
            The tenant slug.

        Returns
        -------
        uuid.UUID or None
            The tenant ID if found and active.
        """
        stmt = select(Tenant.id).where(
            Tenant.slug == slug,
            Tenant.is_active == True,  # noqa: E712
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _get_host(request: Request) -> str:
        """Extract the host from the request, stripping port.

        Parameters
        ----------
        request : Request
            The incoming HTTP request.

        Returns
        -------
        str
            The hostname (lowercase, no port).
        """
        host = request.headers.get("host", "")
        # Strip port if present
        if ":" in host:
            host = host.split(":")[0]
        return host.lower()

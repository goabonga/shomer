# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Tenant trust policy evaluation and management service.

Evaluates whether a user can access a tenant based on the tenant's
trust mode (NONE/ALL/MEMBERS_ONLY/SPECIFIC) and manages trust CRUD.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shomer.models.tenant import Tenant, TenantTrustMode
from shomer.models.tenant_member import TenantMember
from shomer.models.tenant_trusted_source import TenantTrustedSource
from shomer.models.user import User

logger = logging.getLogger(__name__)


class TrustPolicyService:
    """Evaluate and manage tenant trust policies.

    Attributes
    ----------
    session : AsyncSession
        Database session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Trust evaluation ──────────────────────────────────────────────

    async def can_user_access_tenant(
        self,
        user: User,
        tenant_id: uuid.UUID,
    ) -> tuple[bool, str | None]:
        """Check if a user can access a tenant based on trust policies.

        Parameters
        ----------
        user : User
            The authenticated user.
        tenant_id : uuid.UUID
            The target tenant ID.

        Returns
        -------
        tuple[bool, str | None]
            ``(allowed, error_message)``.
        """
        stmt = (
            select(Tenant)
            .where(Tenant.id == tenant_id)
            .options(selectinload(Tenant.trusted_sources))
        )
        result = await self.session.execute(stmt)
        tenant = result.scalar_one_or_none()

        if not tenant:
            logger.warning("Trust check failed: tenant not found: %s", tenant_id)
            return False, "Organization not found"

        if not tenant.is_active:
            logger.warning("Trust check failed: tenant inactive: %s", tenant.slug)
            return False, "This organization is currently inactive"

        match tenant.trust_mode:
            case TenantTrustMode.NONE:
                if user.registration_tenant_id == tenant_id:
                    return True, None
                if await self._is_tenant_member(user.id, tenant_id):
                    return True, None
                return False, "You must be registered on this organization to sign in"

            case TenantTrustMode.ALL:
                return True, None

            case TenantTrustMode.MEMBERS_ONLY:
                if await self._is_tenant_member(user.id, tenant_id):
                    return True, None
                return False, "You must be a member of this organization to sign in"

            case TenantTrustMode.SPECIFIC:
                if self._is_from_trusted_source(
                    user.registration_tenant_id,
                    tenant.trusted_sources,
                ):
                    return True, None
                if await self._is_tenant_member(user.id, tenant_id):
                    return True, None
                return (
                    False,
                    "Your account is not authorized to sign in to this organization",
                )

            case _:
                logger.error(
                    "Unknown trust mode: %s for tenant %s",
                    tenant.trust_mode,
                    tenant_id,
                )
                return False, "Configuration error"

    async def _is_tenant_member(self, user_id: uuid.UUID, tenant_id: uuid.UUID) -> bool:
        """Check if user is a member of the tenant.

        Parameters
        ----------
        user_id : uuid.UUID
            The user ID.
        tenant_id : uuid.UUID
            The tenant ID.

        Returns
        -------
        bool
            True if the user is a member.
        """
        stmt = select(TenantMember.id).where(
            TenantMember.user_id == user_id,
            TenantMember.tenant_id == tenant_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    @staticmethod
    def _is_from_trusted_source(
        registration_tenant_id: uuid.UUID | None,
        trusted_sources: list[TenantTrustedSource],
    ) -> bool:
        """Check if user's registration tenant is trusted.

        Parameters
        ----------
        registration_tenant_id : uuid.UUID or None
            The tenant where the user registered.
        trusted_sources : list[TenantTrustedSource]
            Trusted source configurations.

        Returns
        -------
        bool
            True if the user's origin is trusted.
        """
        if registration_tenant_id is None:
            return False
        return any(
            s.trusted_tenant_id == registration_tenant_id for s in trusted_sources
        )

    # ── Trust config ──────────────────────────────────────────────────

    async def get_tenant_trust_config(
        self, tenant_id: uuid.UUID
    ) -> dict[str, Any] | None:
        """Get the full trust configuration for a tenant.

        Parameters
        ----------
        tenant_id : uuid.UUID
            The tenant ID.

        Returns
        -------
        dict or None
            Trust config dict, or None if tenant not found.
        """
        stmt = (
            select(Tenant)
            .where(Tenant.id == tenant_id)
            .options(
                selectinload(Tenant.trusted_sources).selectinload(
                    TenantTrustedSource.trusted_tenant
                )
            )
        )
        result = await self.session.execute(stmt)
        tenant = result.scalar_one_or_none()

        if not tenant:
            return None

        sources = []
        for s in tenant.trusted_sources:
            sources.append(
                {
                    "id": str(s.id),
                    "trusted_tenant_id": str(s.trusted_tenant_id),
                    "trusted_tenant_name": (
                        s.trusted_tenant.display_name if s.trusted_tenant else "Unknown"
                    ),
                    "trusted_tenant_slug": (
                        s.trusted_tenant.slug if s.trusted_tenant else None
                    ),
                    "is_platform": (
                        s.trusted_tenant.is_platform if s.trusted_tenant else False
                    ),
                    "description": s.description,
                }
            )

        return {
            "trust_mode": tenant.trust_mode.value,
            "trusted_sources": sources,
        }

    # ── Trust CRUD ────────────────────────────────────────────────────

    async def update_trust_mode(
        self, tenant_id: uuid.UUID, trust_mode: TenantTrustMode
    ) -> bool:
        """Update the trust mode for a tenant.

        Parameters
        ----------
        tenant_id : uuid.UUID
            The tenant ID.
        trust_mode : TenantTrustMode
            New trust mode.

        Returns
        -------
        bool
            True if updated.
        """
        stmt = select(Tenant).where(Tenant.id == tenant_id)
        result = await self.session.execute(stmt)
        tenant = result.scalar_one_or_none()
        if not tenant:
            return False

        tenant.trust_mode = trust_mode
        await self.session.flush()
        logger.info(
            "Trust mode updated: tenant=%s mode=%s", tenant_id, trust_mode.value
        )
        return True

    async def add_trusted_source(
        self,
        tenant_id: uuid.UUID,
        trusted_tenant_id: uuid.UUID,
        description: str | None = None,
    ) -> TenantTrustedSource | None:
        """Add a trusted source tenant.

        Parameters
        ----------
        tenant_id : uuid.UUID
            The tenant to configure.
        trusted_tenant_id : uuid.UUID
            The trusted source tenant.
        description : str or None
            Optional description.

        Returns
        -------
        TenantTrustedSource or None
            Created record, or None if already exists.
        """
        stmt = select(TenantTrustedSource).where(
            TenantTrustedSource.tenant_id == tenant_id,
            TenantTrustedSource.trusted_tenant_id == trusted_tenant_id,
        )
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none() is not None:
            return None

        source = TenantTrustedSource(
            tenant_id=tenant_id,
            trusted_tenant_id=trusted_tenant_id,
            description=description,
        )
        self.session.add(source)
        await self.session.flush()
        logger.info(
            "Trusted source added: tenant=%s trusted=%s", tenant_id, trusted_tenant_id
        )
        return source

    async def remove_trusted_source(
        self, tenant_id: uuid.UUID, source_id: uuid.UUID
    ) -> bool:
        """Remove a trusted source.

        Parameters
        ----------
        tenant_id : uuid.UUID
            The tenant ID (for authorization).
        source_id : uuid.UUID
            The trusted source record ID.

        Returns
        -------
        bool
            True if removed.
        """
        stmt = select(TenantTrustedSource).where(
            TenantTrustedSource.id == source_id,
            TenantTrustedSource.tenant_id == tenant_id,
        )
        result = await self.session.execute(stmt)
        source = result.scalar_one_or_none()
        if not source:
            return False

        await self.session.delete(source)
        await self.session.flush()
        logger.info("Trusted source removed: id=%s tenant=%s", source_id, tenant_id)
        return True

    async def get_available_tenants_for_trust(
        self, tenant_id: uuid.UUID
    ) -> list[dict[str, Any]]:
        """Get tenants that can be added as trusted sources.

        Parameters
        ----------
        tenant_id : uuid.UUID
            The current tenant (excluded from results).

        Returns
        -------
        list[dict]
            Available tenants with id, slug, display_name, is_platform.
        """
        # Get currently trusted IDs
        stmt = select(TenantTrustedSource.trusted_tenant_id).where(
            TenantTrustedSource.tenant_id == tenant_id
        )
        result = await self.session.execute(stmt)
        trusted_ids = {row for row in result.scalars().all() if row is not None}
        trusted_ids.add(tenant_id)  # Exclude self

        # Get all active tenants not already trusted
        stmt2 = (
            select(Tenant)
            .where(
                Tenant.is_active == True,  # noqa: E712
                Tenant.id.notin_(trusted_ids),
            )
            .order_by(Tenant.is_platform.desc(), Tenant.display_name)
        )
        result2 = await self.session.execute(stmt2)
        tenants = result2.scalars().all()

        return [
            {
                "id": str(t.id),
                "slug": t.slug,
                "display_name": t.display_name,
                "is_platform": t.is_platform,
            }
            for t in tenants
        ]

    # ── Platform tenant ───────────────────────────────────────────────

    async def get_platform_tenant(self) -> Tenant | None:
        """Get the platform (root) tenant.

        Returns
        -------
        Tenant or None
            The platform tenant, or None if not configured.
        """
        stmt = select(Tenant).where(Tenant.is_platform == True)  # noqa: E712
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def is_platform_trusted(self, tenant_id: uuid.UUID) -> bool:
        """Check if the platform tenant is trusted by a tenant.

        Parameters
        ----------
        tenant_id : uuid.UUID
            The tenant to check.

        Returns
        -------
        bool
            True if platform is in trusted sources.
        """
        platform = await self.get_platform_tenant()
        if not platform:
            return False

        stmt = select(TenantTrustedSource.id).where(
            TenantTrustedSource.tenant_id == tenant_id,
            TenantTrustedSource.trusted_tenant_id == platform.id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

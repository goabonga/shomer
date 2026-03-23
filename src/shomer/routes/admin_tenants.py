# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Admin tenant management API endpoints.

CRUD tenants, members, branding, identity providers, and custom domains.
Requires ``admin:tenants:read`` or ``admin:tenants:write`` scope.
"""

from __future__ import annotations

import uuid as _uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select

from shomer.deps import DbSession
from shomer.middleware.rbac import require_scope
from shomer.models.identity_provider import IdentityProvider
from shomer.models.tenant import Tenant
from shomer.models.tenant_branding import TenantBranding
from shomer.models.tenant_member import TenantMember

router = APIRouter(prefix="/admin/tenants", tags=["admin"])


def _parse_uuid(value: str, label: str = "ID") -> _uuid.UUID:
    """Parse a UUID string or raise 400."""
    try:
        return _uuid.UUID(value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {label}"
        )


def _trust_mode_str(t: Any) -> str:
    """Return trust_mode as plain string."""
    m = t.trust_mode
    return m.value if hasattr(m, "value") else str(m)


def _tenant_summary(t: Any) -> dict[str, Any]:
    """Serialize a Tenant to a summary dict."""
    return {
        "id": str(t.id),
        "slug": t.slug,
        "name": t.name,
        "display_name": t.display_name,
        "is_active": t.is_active,
        "is_platform": t.is_platform,
        "trust_mode": _trust_mode_str(t),
        "custom_domain": t.custom_domain,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


# ---------------------------------------------------------------------------
# Tenants CRUD
# ---------------------------------------------------------------------------


class TenantCreateRequest(BaseModel):
    """Request body for tenant creation.

    Attributes
    ----------
    slug : str
        Unique URL-safe identifier.
    name : str
        Internal name.
    display_name : str
        Human-readable display name.
    trust_mode : str
        Trust mode (none, all, members_only, specific).
    """

    slug: str
    name: str
    display_name: str = ""
    trust_mode: str = "none"


class TenantUpdateRequest(BaseModel):
    """Request body for tenant update.

    Attributes
    ----------
    name : str or None
        Internal name.
    display_name : str or None
        Display name.
    is_active : bool or None
        Active status.
    trust_mode : str or None
        Trust mode.
    """

    name: str | None = None
    display_name: str | None = None
    is_active: bool | None = None
    trust_mode: str | None = None


@router.get(
    "",
    dependencies=[Depends(require_scope("admin:tenants:read"))],
)
async def list_tenants(
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> JSONResponse:
    """List all tenants with pagination.

    Parameters
    ----------
    db : DbSession
        Database session.
    page : int
        Page number.
    page_size : int
        Items per page.

    Returns
    -------
    JSONResponse
        Paginated tenant list.
    """
    from sqlalchemy import func

    count_result = await db.execute(select(func.count()).select_from(Tenant))
    total = count_result.scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        select(Tenant)
        .order_by(Tenant.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    tenants = list(result.scalars().all())

    return JSONResponse(
        content={
            "items": [_tenant_summary(t) for t in tenants],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.post(
    "",
    dependencies=[Depends(require_scope("admin:tenants:write"))],
    status_code=status.HTTP_201_CREATED,
)
async def create_tenant(body: TenantCreateRequest, db: DbSession) -> JSONResponse:
    """Create a new tenant.

    Parameters
    ----------
    body : TenantCreateRequest
        Tenant data.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Created tenant.

    Raises
    ------
    HTTPException
        409 if slug already exists.
    """
    existing = await db.execute(select(Tenant).where(Tenant.slug == body.slug))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Slug already exists"
        )

    from shomer.models.tenant import TenantTrustMode

    try:
        trust = TenantTrustMode(body.trust_mode)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid trust_mode: {body.trust_mode}",
        )

    tenant = Tenant(
        slug=body.slug,
        name=body.name,
        display_name=body.display_name or body.name,
        trust_mode=trust,
    )
    db.add(tenant)
    await db.flush()

    return JSONResponse(
        status_code=201,
        content={**_tenant_summary(tenant), "message": "Tenant created successfully"},
    )


@router.get(
    "/{tenant_id}",
    dependencies=[Depends(require_scope("admin:tenants:read"))],
)
async def get_tenant(tenant_id: str, db: DbSession) -> JSONResponse:
    """Get tenant details.

    Parameters
    ----------
    tenant_id : str
        UUID of the tenant.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Tenant details with settings.

    Raises
    ------
    HTTPException
        404 if not found.
    """
    tid = _parse_uuid(tenant_id, "tenant ID")
    result = await db.execute(select(Tenant).where(Tenant.id == tid))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
        )
    data = _tenant_summary(tenant)
    data["settings"] = tenant.settings
    return JSONResponse(content=data)


@router.put(
    "/{tenant_id}",
    dependencies=[Depends(require_scope("admin:tenants:write"))],
)
async def update_tenant(
    tenant_id: str, body: TenantUpdateRequest, db: DbSession
) -> JSONResponse:
    """Update tenant settings.

    Parameters
    ----------
    tenant_id : str
        UUID of the tenant.
    body : TenantUpdateRequest
        Fields to update.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Updated tenant.

    Raises
    ------
    HTTPException
        404 if not found.
    """
    tid = _parse_uuid(tenant_id, "tenant ID")
    result = await db.execute(select(Tenant).where(Tenant.id == tid))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
        )

    if body.name is not None:
        tenant.name = body.name
    if body.display_name is not None:
        tenant.display_name = body.display_name
    if body.is_active is not None:
        tenant.is_active = body.is_active
    if body.trust_mode is not None:
        from shomer.models.tenant import TenantTrustMode

        try:
            tenant.trust_mode = TenantTrustMode(body.trust_mode)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid trust_mode: {body.trust_mode}",
            )

    await db.flush()
    return JSONResponse(
        content={**_tenant_summary(tenant), "message": "Tenant updated successfully"}
    )


@router.delete(
    "/{tenant_id}",
    dependencies=[Depends(require_scope("admin:tenants:write"))],
)
async def delete_tenant(tenant_id: str, db: DbSession) -> JSONResponse:
    """Delete a tenant.

    Parameters
    ----------
    tenant_id : str
        UUID of the tenant.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Confirmation message.

    Raises
    ------
    HTTPException
        400 if platform tenant, 404 if not found.
    """
    tid = _parse_uuid(tenant_id, "tenant ID")
    result = await db.execute(select(Tenant).where(Tenant.id == tid))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
        )
    if tenant.is_platform:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete platform tenant",
        )
    await db.delete(tenant)
    await db.flush()
    return JSONResponse(
        content={"id": str(tid), "message": "Tenant deleted successfully"}
    )


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------


class MemberRequest(BaseModel):
    """Request body for adding a tenant member.

    Attributes
    ----------
    user_id : str
        UUID of the user to add.
    role : str
        Member role (e.g. owner, admin, member).
    """

    user_id: str
    role: str = "member"


@router.get(
    "/{tenant_id}/members",
    dependencies=[Depends(require_scope("admin:tenants:read"))],
)
async def list_members(tenant_id: str, db: DbSession) -> JSONResponse:
    """List tenant members.

    Parameters
    ----------
    tenant_id : str
        UUID of the tenant.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        List of members.
    """
    tid = _parse_uuid(tenant_id, "tenant ID")
    result = await db.execute(select(TenantMember).where(TenantMember.tenant_id == tid))
    members = list(result.scalars().all())
    return JSONResponse(
        content={
            "items": [
                {
                    "id": str(m.id),
                    "user_id": str(m.user_id),
                    "role": m.role,
                    "joined_at": m.joined_at.isoformat() if m.joined_at else None,
                }
                for m in members
            ],
            "total": len(members),
        }
    )


@router.post(
    "/{tenant_id}/members",
    dependencies=[Depends(require_scope("admin:tenants:write"))],
    status_code=status.HTTP_201_CREATED,
)
async def add_member(
    tenant_id: str, body: MemberRequest, db: DbSession
) -> JSONResponse:
    """Add a member to a tenant.

    Parameters
    ----------
    tenant_id : str
        UUID of the tenant.
    body : MemberRequest
        Member data.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Confirmation message.

    Raises
    ------
    HTTPException
        409 if already a member.
    """
    tid = _parse_uuid(tenant_id, "tenant ID")
    uid = _parse_uuid(body.user_id, "user ID")

    existing = await db.execute(
        select(TenantMember).where(
            TenantMember.tenant_id == tid, TenantMember.user_id == uid
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User is already a member"
        )

    member = TenantMember(
        tenant_id=tid,
        user_id=uid,
        role=body.role,
        joined_at=datetime.now(timezone.utc),
    )
    db.add(member)
    await db.flush()
    return JSONResponse(
        status_code=201, content={"message": "Member added successfully"}
    )


@router.delete(
    "/{tenant_id}/members/{user_id}",
    dependencies=[Depends(require_scope("admin:tenants:write"))],
)
async def remove_member(tenant_id: str, user_id: str, db: DbSession) -> JSONResponse:
    """Remove a member from a tenant.

    Parameters
    ----------
    tenant_id : str
        UUID of the tenant.
    user_id : str
        UUID of the user to remove.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Confirmation message.

    Raises
    ------
    HTTPException
        404 if membership not found.
    """
    tid = _parse_uuid(tenant_id, "tenant ID")
    uid = _parse_uuid(user_id, "user ID")

    result = await db.execute(
        select(TenantMember).where(
            TenantMember.tenant_id == tid, TenantMember.user_id == uid
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
        )
    await db.delete(member)
    await db.flush()
    return JSONResponse(content={"message": "Member removed successfully"})


# ---------------------------------------------------------------------------
# Branding
# ---------------------------------------------------------------------------


class BrandingUpdateRequest(BaseModel):
    """Request body for branding update.

    Attributes
    ----------
    logo_url : str or None
        Logo URL.
    primary_color : str or None
        Primary brand color (hex).
    secondary_color : str or None
        Secondary brand color (hex).
    """

    logo_url: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None


@router.put(
    "/{tenant_id}/branding",
    dependencies=[Depends(require_scope("admin:tenants:write"))],
)
async def update_branding(
    tenant_id: str, body: BrandingUpdateRequest, db: DbSession
) -> JSONResponse:
    """Update tenant branding.

    Creates the branding record if it doesn't exist.

    Parameters
    ----------
    tenant_id : str
        UUID of the tenant.
    body : BrandingUpdateRequest
        Branding fields.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Updated branding.
    """
    tid = _parse_uuid(tenant_id, "tenant ID")

    result = await db.execute(
        select(TenantBranding).where(TenantBranding.tenant_id == tid)
    )
    branding = result.scalar_one_or_none()

    if branding is None:
        branding = TenantBranding(tenant_id=tid)
        db.add(branding)

    if body.logo_url is not None:
        branding.logo_url = body.logo_url
    if body.primary_color is not None:
        branding.primary_color = body.primary_color
    if body.secondary_color is not None:
        branding.secondary_color = body.secondary_color

    await db.flush()
    return JSONResponse(
        content={
            "tenant_id": str(tid),
            "logo_url": branding.logo_url,
            "primary_color": branding.primary_color,
            "secondary_color": branding.secondary_color,
            "message": "Branding updated successfully",
        }
    )


# ---------------------------------------------------------------------------
# Identity Providers
# ---------------------------------------------------------------------------


class IdPCreateRequest(BaseModel):
    """Request body for creating an identity provider.

    Attributes
    ----------
    name : str
        Provider display name.
    provider_type : str
        Type (oidc, saml, google, github, microsoft).
    client_id : str
        OAuth2 client ID.
    """

    name: str
    provider_type: str
    client_id: str


@router.get(
    "/{tenant_id}/idps",
    dependencies=[Depends(require_scope("admin:tenants:read"))],
)
async def list_idps(tenant_id: str, db: DbSession) -> JSONResponse:
    """List identity providers for a tenant.

    Parameters
    ----------
    tenant_id : str
        UUID of the tenant.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        List of IdPs.
    """
    tid = _parse_uuid(tenant_id, "tenant ID")
    result = await db.execute(
        select(IdentityProvider).where(IdentityProvider.tenant_id == tid)
    )
    idps = list(result.scalars().all())

    def _idp_type_str(idp: Any) -> str:
        pt = idp.provider_type
        return pt.value if hasattr(pt, "value") else str(pt)

    return JSONResponse(
        content={
            "items": [
                {
                    "id": str(idp.id),
                    "name": idp.name,
                    "provider_type": _idp_type_str(idp),
                    "client_id": idp.client_id,
                    "is_active": idp.is_active,
                }
                for idp in idps
            ],
            "total": len(idps),
        }
    )


@router.post(
    "/{tenant_id}/idps",
    dependencies=[Depends(require_scope("admin:tenants:write"))],
    status_code=status.HTTP_201_CREATED,
)
async def create_idp(
    tenant_id: str, body: IdPCreateRequest, db: DbSession
) -> JSONResponse:
    """Create an identity provider for a tenant.

    Parameters
    ----------
    tenant_id : str
        UUID of the tenant.
    body : IdPCreateRequest
        IdP data.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Created IdP.
    """
    tid = _parse_uuid(tenant_id, "tenant ID")

    from shomer.models.identity_provider import IdentityProviderType

    try:
        pt = IdentityProviderType(body.provider_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider_type: {body.provider_type}",
        )

    idp = IdentityProvider(
        tenant_id=tid,
        name=body.name,
        provider_type=pt,
        client_id=body.client_id,
    )
    db.add(idp)
    await db.flush()

    return JSONResponse(
        status_code=201,
        content={
            "id": str(idp.id),
            "name": idp.name,
            "provider_type": body.provider_type,
            "message": "Identity provider created successfully",
        },
    )


@router.delete(
    "/{tenant_id}/idps/{idp_id}",
    dependencies=[Depends(require_scope("admin:tenants:write"))],
)
async def delete_idp(tenant_id: str, idp_id: str, db: DbSession) -> JSONResponse:
    """Delete an identity provider.

    Parameters
    ----------
    tenant_id : str
        UUID of the tenant.
    idp_id : str
        UUID of the IdP.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Confirmation message.

    Raises
    ------
    HTTPException
        404 if not found.
    """
    tid = _parse_uuid(tenant_id, "tenant ID")
    iid = _parse_uuid(idp_id, "IdP ID")

    result = await db.execute(
        select(IdentityProvider).where(
            IdentityProvider.id == iid, IdentityProvider.tenant_id == tid
        )
    )
    idp = result.scalar_one_or_none()
    if idp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Identity provider not found",
        )
    await db.delete(idp)
    await db.flush()
    return JSONResponse(
        content={"id": str(iid), "message": "Identity provider deleted successfully"}
    )


# ---------------------------------------------------------------------------
# Custom Domains
# ---------------------------------------------------------------------------


class DomainUpdateRequest(BaseModel):
    """Request body for custom domain update.

    Attributes
    ----------
    custom_domain : str or None
        Custom domain (set to None to remove).
    """

    custom_domain: str | None = None


@router.get(
    "/{tenant_id}/domains",
    dependencies=[Depends(require_scope("admin:tenants:read"))],
)
async def get_domains(tenant_id: str, db: DbSession) -> JSONResponse:
    """Get custom domain for a tenant.

    Parameters
    ----------
    tenant_id : str
        UUID of the tenant.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Domain info.

    Raises
    ------
    HTTPException
        404 if tenant not found.
    """
    tid = _parse_uuid(tenant_id, "tenant ID")
    result = await db.execute(select(Tenant).where(Tenant.id == tid))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
        )
    return JSONResponse(
        content={
            "tenant_id": str(tid),
            "slug": tenant.slug,
            "custom_domain": tenant.custom_domain,
        }
    )


@router.put(
    "/{tenant_id}/domains",
    dependencies=[Depends(require_scope("admin:tenants:write"))],
)
async def update_domains(
    tenant_id: str, body: DomainUpdateRequest, db: DbSession
) -> JSONResponse:
    """Update custom domain for a tenant.

    Parameters
    ----------
    tenant_id : str
        UUID of the tenant.
    body : DomainUpdateRequest
        Domain data.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Updated domain.

    Raises
    ------
    HTTPException
        404 if tenant not found.
    """
    tid = _parse_uuid(tenant_id, "tenant ID")
    result = await db.execute(select(Tenant).where(Tenant.id == tid))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
        )
    tenant.custom_domain = body.custom_domain
    await db.flush()
    return JSONResponse(
        content={
            "tenant_id": str(tid),
            "custom_domain": tenant.custom_domain,
            "message": "Domain updated successfully",
        }
    )

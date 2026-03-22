# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Federation provider listing and authorization initiation endpoints."""

from __future__ import annotations

import base64
import json

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, RedirectResponse

from shomer.deps import DbSession
from shomer.services.federation_service import FederationService

router = APIRouter(prefix="/federation", tags=["federation"])


@router.get("/providers")
async def list_providers(
    db: DbSession,
    request: Request,
    tenant_slug: str | None = Query(
        None, description="Tenant slug (optional if using subdomain)"
    ),
) -> JSONResponse:
    """List available identity providers for a tenant.

    Used by the login UI to display social/SSO login buttons.

    Parameters
    ----------
    db : DbSession
        Database session.
    request : Request
        HTTP request (for tenant context).
    tenant_slug : str or None
        Tenant slug override.

    Returns
    -------
    JSONResponse
        List of active IdPs with name, type, icon, button_text.
    """
    resolved_slug = tenant_slug
    if not resolved_slug:
        tid = getattr(request.state, "tenant_id", None)
        if tid:
            from sqlalchemy import select

            from shomer.models.tenant import Tenant

            stmt = select(Tenant.slug).where(Tenant.id == tid)
            result = await db.execute(stmt)
            resolved_slug = result.scalar_one_or_none()

    if not resolved_slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant not specified. Use subdomain, path prefix, or tenant_slug parameter.",
        )

    svc = FederationService(db)
    providers = await svc.get_tenant_identity_providers(resolved_slug)

    return JSONResponse(
        content={
            "tenant_slug": resolved_slug,
            "providers": [
                {
                    "id": str(idp.id),
                    "name": idp.name,
                    "provider_type": (
                        idp.provider_type.value
                        if hasattr(idp.provider_type, "value")
                        else str(idp.provider_type)
                    ),
                    "icon_url": idp.icon_url,
                    "button_text": idp.button_text or f"Continue with {idp.name}",
                }
                for idp in providers
            ],
            "local_login_enabled": True,
        },
    )


@router.get("/{idp_id}/authorize")
async def initiate_federation(
    request: Request,
    idp_id: str,
    db: DbSession,
    redirect_uri: str | None = Query(None),
    state: str | None = Query(None),
) -> RedirectResponse:
    """Initiate federation flow with an external identity provider.

    Redirects the user to the external IdP for authentication.

    Parameters
    ----------
    request : Request
        HTTP request.
    idp_id : str
        Identity provider ID.
    db : DbSession
        Database session.
    redirect_uri : str or None
        Where to redirect after authentication.
    state : str or None
        State to preserve through the flow.

    Returns
    -------
    RedirectResponse
        Redirect to the IdP authorization endpoint.
    """
    # Resolve tenant slug from context
    tenant_slug: str | None = None
    tid = getattr(request.state, "tenant_id", None)
    if tid:
        from sqlalchemy import select

        from shomer.models.tenant import Tenant

        stmt = select(Tenant.slug).where(Tenant.id == tid)
        result = await db.execute(stmt)
        tenant_slug = result.scalar_one_or_none()

    if not tenant_slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required for federation",
        )

    svc = FederationService(db)
    idp = await svc.get_identity_provider(idp_id)
    if not idp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Identity provider not found",
        )
    if not idp.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identity provider is not active",
        )

    # Generate security parameters
    nonce = FederationService.generate_nonce()
    code_verifier = FederationService.generate_code_verifier()
    internal_state = FederationService.generate_state()

    # Build callback URL
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.url.netloc)
    callback_url = f"{scheme}://{host}/federation/callback"

    # Encode state
    state_data = {
        "tenant_slug": tenant_slug,
        "idp_id": str(idp.id),
        "nonce": nonce,
        "code_verifier": code_verifier,
        "original_state": state,
        "redirect_uri": redirect_uri,
        "internal_state": internal_state,
    }
    encoded_state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

    auth_url = await svc.get_authorization_url(
        idp=idp,
        callback_url=callback_url,
        state=encoded_state,
        nonce=nonce,
        code_verifier=code_verifier,
    )

    return RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Federation provider listing, authorization initiation, and callback endpoints."""

from __future__ import annotations

import base64
import json
import logging

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, RedirectResponse

from shomer.deps import DbSession
from shomer.services.federation_service import FederationService

logger = logging.getLogger(__name__)

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


@router.get("/callback")
async def federation_callback(
    request: Request,
    db: DbSession,
    code: str | None = Query(None),
    state: str | None = Query(None),
    error: str | None = Query(None),
    error_description: str | None = Query(None),
) -> RedirectResponse:
    """Handle callback from external identity provider.

    Receives the authorization code, exchanges it for tokens,
    extracts user info, performs JIT provisioning or account linking,
    creates a session, and redirects to the original URI.

    All errors redirect gracefully to the login page — never returns 500.

    Parameters
    ----------
    request : Request
        HTTP request.
    db : DbSession
        Database session.
    code : str or None
        Authorization code from IdP.
    state : str or None
        Encoded state parameter.
    error : str or None
        Error code from IdP.
    error_description : str or None
        Error description from IdP.

    Returns
    -------
    RedirectResponse
        Redirect to the original URI or login page.
    """
    # 1. Handle IdP error responses
    if error:
        logger.warning(
            "Federation error from IdP: error=%s, description=%s",
            error,
            error_description,
        )
        msg = error_description or error
        return RedirectResponse(
            url=f"/ui/login?error=federation_failed&message={msg}",
            status_code=status.HTTP_302_FOUND,
        )

    # 2. Validate required parameters
    if not code or not state:
        return RedirectResponse(
            url="/ui/login?error=federation_failed&message=Missing+code+or+state",
            status_code=status.HTTP_302_FOUND,
        )

    # 3. Decode state
    try:
        state_data = json.loads(base64.urlsafe_b64decode(state).decode())
    except (ValueError, json.JSONDecodeError) as exc:
        logger.error("Failed to decode federation state: %s", exc)
        return RedirectResponse(
            url="/ui/login?error=federation_failed&message=Invalid+state",
            status_code=status.HTTP_302_FOUND,
        )

    tenant_slug = state_data.get("tenant_slug")
    idp_id = state_data.get("idp_id")
    code_verifier = state_data.get("code_verifier")
    original_state = state_data.get("original_state")
    redirect_uri = state_data.get("redirect_uri")

    if not tenant_slug or not idp_id:
        return RedirectResponse(
            url="/ui/login?error=federation_failed&message=Invalid+state+data",
            status_code=status.HTTP_302_FOUND,
        )

    # 4. Look up IdP
    svc = FederationService(db)
    idp = await svc.get_identity_provider(idp_id)
    if not idp:
        return RedirectResponse(
            url="/ui/login?error=federation_failed&message=Provider+not+found",
            status_code=status.HTTP_302_FOUND,
        )

    # 5. Build callback URL (must match authorization request)
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.url.netloc)
    callback_url = f"{scheme}://{host}/federation/callback"

    try:
        # 6. Exchange code for tokens
        logger.info("Exchanging authorization code: idp=%s", idp.name)
        token_response = await svc.exchange_code_for_tokens(
            idp=idp,
            code=code,
            callback_url=callback_url,
            code_verifier=code_verifier,
        )

        access_token = token_response.get("access_token")
        id_token_value = token_response.get("id_token")
        if not access_token:
            raise ValueError("No access token in IdP response")

        # 7. Get user info
        logger.info("Fetching user info: idp=%s", idp.name)
        user_info = await svc.get_user_info(
            idp=idp,
            access_token=access_token,
            id_token=id_token_value,
        )
        logger.info(
            "User info received: subject=%s, email=%s",
            user_info.subject,
            user_info.email,
        )

        # 8. JIT provisioning / account linking
        user, _fed_id, is_new = await svc.find_or_create_user(
            idp=idp,
            user_info=user_info,
            tenant_slug=tenant_slug,
        )
        logger.info(
            "User authenticated via federation: user_id=%s, new=%s, idp=%s",
            user.id,
            is_new,
            idp.name,
        )

        # 9. Create session
        from shomer.middleware.cookies import get_cookie_policy
        from shomer.services.session_service import SessionService

        session_svc = SessionService(db)
        session, raw_token = await session_svc.create(
            user_id=user.id,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
        )
        await db.flush()

        # 10. Determine redirect
        if redirect_uri:
            final_redirect = redirect_uri
            if original_state:
                sep = "&" if "?" in final_redirect else "?"
                final_redirect = f"{final_redirect}{sep}state={original_state}"
        else:
            final_redirect = "/ui/settings/profile"

        # 11. Set cookies and redirect
        from shomer.core.settings import get_settings

        policy = get_cookie_policy(get_settings())
        response = RedirectResponse(
            url=final_redirect, status_code=status.HTTP_302_FOUND
        )
        response.set_cookie(
            key="session_id",
            value=raw_token,
            httponly=policy.httponly,
            secure=policy.secure,
            samesite=policy.samesite,
            domain=policy.domain or None,
            max_age=86400,
        )
        response.set_cookie(
            key="csrf_token",
            value=session.csrf_token,
            httponly=False,
            secure=policy.secure,
            samesite=policy.samesite,
            domain=policy.domain or None,
            max_age=86400,
        )
        return response

    except ValueError as exc:
        logger.error("Federation failed: %s", exc)
        return RedirectResponse(
            url=f"/ui/login?error=federation_failed&message={exc}",
            status_code=status.HTTP_302_FOUND,
        )
    except Exception as exc:
        logger.exception("Unexpected error during federation: %s", exc)
        return RedirectResponse(
            url="/ui/login?error=federation_failed&message=An+unexpected+error+occurred",
            status_code=status.HTTP_302_FOUND,
        )

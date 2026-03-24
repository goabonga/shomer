# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Browser-facing organisation/tenant management UI routes (Jinja2/HTMX).

Self-service organisation management pages within the user settings area.
Allows users to list, create, view and manage their own organisations.
"""

from __future__ import annotations

import re
import uuid as uuid_mod
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from shomer.deps import DbSession
from shomer.models.tenant import Tenant, TenantTrustMode
from shomer.models.tenant_member import TenantMember
from shomer.models.user import User
from shomer.services.session_service import SessionService

router = APIRouter(prefix="/ui/settings", tags=["ui"], include_in_schema=False)


def _templates() -> Jinja2Templates:
    """Get the Jinja2 templates instance."""
    from shomer.app import templates

    return templates


def _render(request: Request, template: str, ctx: dict[str, Any] | None = None) -> Any:
    """Render a template with the given context.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    template : str
        Template path relative to the templates directory.
    ctx : dict or None
        Template context variables.

    Returns
    -------
    Any
        Jinja2 template response.
    """
    return _templates().TemplateResponse(request, template, ctx or {})


async def _get_session_user(request: Request, db: Any) -> tuple[Any, Any] | None:
    """Validate session and return (session, user) or None.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : AsyncSession
        Database session.

    Returns
    -------
    tuple or None
        (session, user) if authenticated, None otherwise.
    """
    session_token = request.cookies.get("session_id")
    if not session_token:
        return None

    svc = SessionService(db)
    session = await svc.validate(session_token)
    if session is None:
        return None

    stmt = (
        select(User)
        .where(User.id == session.user_id)
        .options(selectinload(User.profile), selectinload(User.emails))
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        return None

    return session, user


@router.get("/organisations", response_class=HTMLResponse)
async def settings_organisations(request: Request, db: DbSession) -> Any:
    """Render the organisations list page.

    Shows all organisations the authenticated user is a member of,
    along with their role in each organisation.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.

    Returns
    -------
    HTMLResponse
        Organisations list page or redirect to login.
    """
    auth = await _get_session_user(request, db)
    if auth is None:
        return RedirectResponse(
            url="/ui/login?next=/ui/settings/organisations", status_code=302
        )

    _, user = auth

    # Fetch memberships with tenant details
    stmt = (
        select(TenantMember)
        .where(TenantMember.user_id == user.id)
        .options(selectinload(TenantMember.tenant))
        .order_by(TenantMember.joined_at.desc())
    )
    result = await db.execute(stmt)
    memberships = list(result.scalars().all())

    # Build org list with role info
    organisations: list[dict[str, Any]] = []
    for membership in memberships:
        tenant: Tenant = membership.tenant
        organisations.append(
            {
                "id": str(tenant.id),
                "slug": tenant.slug,
                "name": tenant.name,
                "display_name": tenant.display_name,
                "is_active": tenant.is_active,
                "is_platform": tenant.is_platform,
                "role": membership.role,
                "joined_at": membership.joined_at,
            }
        )

    return _render(
        request,
        "settings/organisations.html",
        {
            "user": user,
            "organisations": organisations,
            "section": "organisations",
        },
    )


#: Regex for valid organisation slugs (lowercase alphanumeric + hyphens).
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$")


@router.get("/organisations/new", response_class=HTMLResponse)
async def settings_organisation_new(request: Request, db: DbSession) -> Any:
    """Render the create organisation form.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.

    Returns
    -------
    HTMLResponse
        Organisation creation form or redirect to login.
    """
    auth = await _get_session_user(request, db)
    if auth is None:
        return RedirectResponse(
            url="/ui/login?next=/ui/settings/organisations/new", status_code=302
        )

    _, user = auth
    return _render(
        request,
        "settings/organisation_form.html",
        {
            "user": user,
            "section": "organisations",
            "trust_modes": [m.value for m in TenantTrustMode],
            "error": None,
        },
    )


@router.post("/organisations/new", response_class=HTMLResponse)
async def settings_organisation_create(
    request: Request,
    db: DbSession,
    slug: str = Form(...),
    name: str = Form(...),
    display_name: str = Form(""),
    trust_mode: str = Form("none"),
) -> Any:
    """Handle organisation creation form submission.

    Validates the slug, creates the tenant, and adds the current user
    as the owner.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.
    slug : str
        Unique URL-safe identifier for the organisation.
    name : str
        Internal name.
    display_name : str
        Human-readable display name.
    trust_mode : str
        Trust mode (none, all, members_only, specific).

    Returns
    -------
    HTMLResponse
        Redirect to org detail on success, or form with error.
    """
    auth = await _get_session_user(request, db)
    if auth is None:
        return RedirectResponse(
            url="/ui/login?next=/ui/settings/organisations/new", status_code=302
        )

    _, user = auth

    def _form_error(msg: str) -> Any:
        return _render(
            request,
            "settings/organisation_form.html",
            {
                "user": user,
                "section": "organisations",
                "trust_modes": [m.value for m in TenantTrustMode],
                "error": msg,
                "form_slug": slug,
                "form_name": name,
                "form_display_name": display_name,
                "form_trust_mode": trust_mode,
            },
        )

    # Validate slug format
    if not _SLUG_RE.match(slug):
        return _form_error(
            "Invalid slug. Use 3-63 lowercase letters, digits, and hyphens."
        )

    # Check slug uniqueness
    existing = await db.execute(select(Tenant).where(Tenant.slug == slug))
    if existing.scalar_one_or_none() is not None:
        return _form_error("This slug is already taken.")

    # Validate trust mode
    try:
        trust = TenantTrustMode(trust_mode)
    except ValueError:
        return _form_error(f"Invalid trust mode: {trust_mode}")

    # Create tenant
    tenant = Tenant(
        slug=slug,
        name=name,
        display_name=display_name or name,
        trust_mode=trust,
    )
    db.add(tenant)
    await db.flush()

    # Add current user as owner
    membership = TenantMember(
        user_id=user.id,
        tenant_id=tenant.id,
        role="owner",
        joined_at=datetime.now(timezone.utc),
    )
    db.add(membership)
    await db.flush()

    return RedirectResponse(
        url=f"/ui/settings/organisations/{tenant.id}",
        status_code=302,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_uuid(value: str) -> uuid_mod.UUID | None:
    """Parse a UUID string, returning None on failure.

    Parameters
    ----------
    value : str
        String to parse.

    Returns
    -------
    uuid.UUID or None
        Parsed UUID or None if invalid.
    """
    try:
        return uuid_mod.UUID(value)
    except ValueError:
        return None


async def _get_membership(
    db: Any, user_id: Any, tenant_id: uuid_mod.UUID
) -> tuple[Any, Any] | None:
    """Fetch the TenantMember and Tenant for a user, or None.

    Parameters
    ----------
    db : AsyncSession
        Database session.
    user_id : uuid.UUID
        The authenticated user ID.
    tenant_id : uuid.UUID
        The tenant to look up.

    Returns
    -------
    tuple or None
        (membership, tenant) if the user is a member, None otherwise.
    """
    stmt = (
        select(TenantMember)
        .where(TenantMember.user_id == user_id, TenantMember.tenant_id == tenant_id)
        .options(selectinload(TenantMember.tenant))
    )
    result = await db.execute(stmt)
    membership = result.scalar_one_or_none()
    if membership is None:
        return None
    return membership, membership.tenant


def _trust_mode_str(tenant: Any) -> str:
    """Return trust_mode as plain string.

    Parameters
    ----------
    tenant : Tenant
        The tenant object.

    Returns
    -------
    str
        Trust mode value.
    """
    m = tenant.trust_mode
    return m.value if hasattr(m, "value") else str(m)


# ---------------------------------------------------------------------------
# Organisation detail / edit
# ---------------------------------------------------------------------------


@router.get("/organisations/{org_id}", response_class=HTMLResponse)
async def settings_organisation_detail(
    request: Request, org_id: str, db: DbSession
) -> Any:
    """Render the organisation detail page.

    Shows organisation information and management options.
    Only accessible to members of the organisation.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    org_id : str
        UUID of the organisation.
    db : DbSession
        Database session.

    Returns
    -------
    HTMLResponse
        Organisation detail page, 404 page, or redirect to login.
    """
    auth = await _get_session_user(request, db)
    if auth is None:
        return RedirectResponse(
            url=f"/ui/login?next=/ui/settings/organisations/{org_id}",
            status_code=302,
        )

    _, user = auth

    tid = _parse_uuid(org_id)
    if tid is None:
        return _render(
            request,
            "settings/organisation_detail.html",
            {
                "user": user,
                "section": "organisations",
                "error": "Invalid organisation ID.",
            },
        )

    result = await _get_membership(db, user.id, tid)
    if result is None:
        return _render(
            request,
            "settings/organisation_detail.html",
            {
                "user": user,
                "section": "organisations",
                "error": "Organisation not found.",
            },
        )

    membership, tenant = result

    return _render(
        request,
        "settings/organisation_detail.html",
        {
            "user": user,
            "section": "organisations",
            "org": {
                "id": str(tenant.id),
                "slug": tenant.slug,
                "name": tenant.name,
                "display_name": tenant.display_name,
                "custom_domain": tenant.custom_domain,
                "is_active": tenant.is_active,
                "is_platform": tenant.is_platform,
                "trust_mode": _trust_mode_str(tenant),
                "created_at": tenant.created_at,
            },
            "role": membership.role,
            "trust_modes": [m.value for m in TenantTrustMode],
            "error": None,
            "success": None,
        },
    )


@router.post("/organisations/{org_id}", response_class=HTMLResponse)
async def settings_organisation_edit(
    request: Request,
    org_id: str,
    db: DbSession,
    name: str = Form(...),
    display_name: str = Form(""),
    trust_mode: str = Form("none"),
) -> Any:
    """Handle organisation edit form submission.

    Only owners and admins can edit organisation details.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    org_id : str
        UUID of the organisation.
    db : DbSession
        Database session.
    name : str
        Updated internal name.
    display_name : str
        Updated display name.
    trust_mode : str
        Updated trust mode.

    Returns
    -------
    HTMLResponse
        Organisation detail page with success/error message, or redirect to login.
    """
    auth = await _get_session_user(request, db)
    if auth is None:
        return RedirectResponse(
            url=f"/ui/login?next=/ui/settings/organisations/{org_id}",
            status_code=302,
        )

    _, user = auth

    tid = _parse_uuid(org_id)
    if tid is None:
        return _render(
            request,
            "settings/organisation_detail.html",
            {
                "user": user,
                "section": "organisations",
                "error": "Invalid organisation ID.",
            },
        )

    result = await _get_membership(db, user.id, tid)
    if result is None:
        return _render(
            request,
            "settings/organisation_detail.html",
            {
                "user": user,
                "section": "organisations",
                "error": "Organisation not found.",
            },
        )

    membership, tenant = result

    def _detail_ctx(
        *,
        error: str | None = None,
        success: str | None = None,
    ) -> dict[str, Any]:
        return {
            "user": user,
            "section": "organisations",
            "org": {
                "id": str(tenant.id),
                "slug": tenant.slug,
                "name": tenant.name,
                "display_name": tenant.display_name,
                "custom_domain": tenant.custom_domain,
                "is_active": tenant.is_active,
                "is_platform": tenant.is_platform,
                "trust_mode": _trust_mode_str(tenant),
                "created_at": tenant.created_at,
            },
            "role": membership.role,
            "trust_modes": [m.value for m in TenantTrustMode],
            "error": error,
            "success": success,
        }

    # Only owners and admins can edit
    if membership.role not in ("owner", "admin"):
        return _render(
            request,
            "settings/organisation_detail.html",
            _detail_ctx(error="You do not have permission to edit this organisation."),
        )

    # Validate trust mode
    try:
        trust = TenantTrustMode(trust_mode)
    except ValueError:
        return _render(
            request,
            "settings/organisation_detail.html",
            _detail_ctx(error=f"Invalid trust mode: {trust_mode}"),
        )

    # Apply changes
    tenant.name = name
    tenant.display_name = display_name or name
    tenant.trust_mode = trust
    await db.flush()

    return _render(
        request,
        "settings/organisation_detail.html",
        _detail_ctx(success="Organisation updated successfully."),
    )


# ---------------------------------------------------------------------------
# Custom domain verification
# ---------------------------------------------------------------------------

#: Regex for a valid domain name.
_DOMAIN_RE = re.compile(
    r"^(?!-)[a-zA-Z0-9-]{1,63}(?<!-)(\.[a-zA-Z0-9-]{1,63})*\.[a-zA-Z]{2,}$"
)


@router.get("/organisations/{org_id}/domains", response_class=HTMLResponse)
async def settings_organisation_domains(
    request: Request, org_id: str, db: DbSession
) -> Any:
    """Render the custom domain management page.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    org_id : str
        UUID of the organisation.
    db : DbSession
        Database session.

    Returns
    -------
    HTMLResponse
        Custom domain page, or redirect to login.
    """
    auth = await _get_session_user(request, db)
    if auth is None:
        return RedirectResponse(
            url=f"/ui/login?next=/ui/settings/organisations/{org_id}/domains",
            status_code=302,
        )

    _, user = auth

    tid = _parse_uuid(org_id)
    if tid is None:
        return _render(
            request,
            "settings/organisation_domains.html",
            {
                "user": user,
                "section": "organisations",
                "error": "Invalid organisation ID.",
            },
        )

    result = await _get_membership(db, user.id, tid)
    if result is None:
        return _render(
            request,
            "settings/organisation_domains.html",
            {
                "user": user,
                "section": "organisations",
                "error": "Organisation not found.",
            },
        )

    membership, tenant = result

    return _render(
        request,
        "settings/organisation_domains.html",
        {
            "user": user,
            "section": "organisations",
            "org": {
                "id": str(tenant.id),
                "slug": tenant.slug,
                "display_name": tenant.display_name,
            },
            "custom_domain": tenant.custom_domain,
            "role": membership.role,
            "error": None,
            "success": None,
        },
    )


@router.post("/organisations/{org_id}/domains", response_class=HTMLResponse)
async def settings_organisation_domains_update(
    request: Request,
    org_id: str,
    db: DbSession,
    custom_domain: str = Form(""),
) -> Any:
    """Handle custom domain update form submission.

    Only owners and admins can update the custom domain.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    org_id : str
        UUID of the organisation.
    db : DbSession
        Database session.
    custom_domain : str
        The custom domain to set (empty to remove).

    Returns
    -------
    HTMLResponse
        Domain page with success/error message, or redirect to login.
    """
    auth = await _get_session_user(request, db)
    if auth is None:
        return RedirectResponse(
            url=f"/ui/login?next=/ui/settings/organisations/{org_id}/domains",
            status_code=302,
        )

    _, user = auth

    tid = _parse_uuid(org_id)
    if tid is None:
        return _render(
            request,
            "settings/organisation_domains.html",
            {
                "user": user,
                "section": "organisations",
                "error": "Invalid organisation ID.",
            },
        )

    result = await _get_membership(db, user.id, tid)
    if result is None:
        return _render(
            request,
            "settings/organisation_domains.html",
            {
                "user": user,
                "section": "organisations",
                "error": "Organisation not found.",
            },
        )

    membership, tenant = result

    def _ctx(*, error: str | None = None, success: str | None = None) -> dict[str, Any]:
        return {
            "user": user,
            "section": "organisations",
            "org": {
                "id": str(tenant.id),
                "slug": tenant.slug,
                "display_name": tenant.display_name,
            },
            "custom_domain": tenant.custom_domain,
            "role": membership.role,
            "error": error,
            "success": success,
        }

    if membership.role not in ("owner", "admin"):
        return _render(
            request,
            "settings/organisation_domains.html",
            _ctx(error="You do not have permission to update domains."),
        )

    domain = custom_domain.strip() or None

    if domain is not None and not _DOMAIN_RE.match(domain):
        return _render(
            request,
            "settings/organisation_domains.html",
            _ctx(error="Invalid domain format."),
        )

    # Check uniqueness if setting a domain
    if domain is not None:
        dup_stmt = select(Tenant).where(
            Tenant.custom_domain == domain, Tenant.id != tid
        )
        dup_result = await db.execute(dup_stmt)
        if dup_result.scalar_one_or_none() is not None:
            return _render(
                request,
                "settings/organisation_domains.html",
                _ctx(error="This domain is already in use by another organisation."),
            )

    tenant.custom_domain = domain
    await db.flush()

    msg = "Custom domain updated." if domain else "Custom domain removed."
    return _render(
        request,
        "settings/organisation_domains.html",
        _ctx(success=msg),
    )

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Browser-facing organisation/tenant management UI routes (Jinja2/HTMX).

Self-service organisation management pages within the user settings area.
Allows users to list, create, view and manage their own organisations.
"""

from __future__ import annotations

import re
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

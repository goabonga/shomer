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
from shomer.models.identity_provider import IdentityProvider, IdentityProviderType
from shomer.models.tenant import Tenant, TenantTrustMode
from shomer.models.tenant_branding import TenantBranding
from shomer.models.tenant_custom_role import TenantCustomRole
from shomer.models.tenant_member import TenantMember
from shomer.models.tenant_template import TenantTemplate
from shomer.models.tenant_trusted_source import TenantTrustedSource
from shomer.models.user import User
from shomer.models.user_email import UserEmail
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


# ---------------------------------------------------------------------------
# Member management
# ---------------------------------------------------------------------------

#: Valid member roles.
_MEMBER_ROLES = ("owner", "admin", "member")


async def _list_members(db: Any, tenant_id: Any) -> list[dict[str, Any]]:
    """Fetch all members for a tenant.

    Parameters
    ----------
    db : AsyncSession
        Database session.
    tenant_id : uuid.UUID
        The tenant ID.

    Returns
    -------
    list
        List of member dicts with user info.
    """
    stmt = (
        select(TenantMember)
        .where(TenantMember.tenant_id == tenant_id)
        .options(selectinload(TenantMember.user))
        .order_by(TenantMember.joined_at)
    )
    result = await db.execute(stmt)
    members_list = list(result.scalars().all())
    items: list[dict[str, Any]] = []
    for m in members_list:
        items.append(
            {
                "id": str(m.id),
                "user_id": str(m.user_id),
                "username": m.user.username if m.user else "unknown",
                "role": m.role,
                "joined_at": m.joined_at,
            }
        )
    return items


@router.get("/organisations/{org_id}/members", response_class=HTMLResponse)
async def settings_organisation_members(
    request: Request, org_id: str, db: DbSession
) -> Any:
    """Render the member management page.

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
        Members page, or redirect to login.
    """
    auth = await _get_session_user(request, db)
    if auth is None:
        return RedirectResponse(
            url=f"/ui/login?next=/ui/settings/organisations/{org_id}/members",
            status_code=302,
        )

    _, user = auth

    tid = _parse_uuid(org_id)
    if tid is None:
        return _render(
            request,
            "settings/organisation_members.html",
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
            "settings/organisation_members.html",
            {
                "user": user,
                "section": "organisations",
                "error": "Organisation not found.",
            },
        )

    membership, tenant = result
    members = await _list_members(db, tid)

    return _render(
        request,
        "settings/organisation_members.html",
        {
            "user": user,
            "section": "organisations",
            "org": {
                "id": str(tenant.id),
                "slug": tenant.slug,
                "display_name": tenant.display_name,
            },
            "members": members,
            "role": membership.role,
            "roles": _MEMBER_ROLES,
            "error": None,
            "success": None,
        },
    )


@router.post("/organisations/{org_id}/members", response_class=HTMLResponse)
async def settings_organisation_members_action(
    request: Request,
    org_id: str,
    db: DbSession,
    action: str = Form(...),
    email: str = Form(""),
    member_role: str = Form("member"),
    member_id: str = Form(""),
) -> Any:
    """Handle member management actions (add, remove, update role).

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    org_id : str
        UUID of the organisation.
    db : DbSession
        Database session.
    action : str
        Action to perform: ``add``, ``remove``, or ``update_role``.
    email : str
        Email address of the user to add.
    member_role : str
        Role to assign (for add and update_role actions).
    member_id : str
        ID of the member to remove or update.

    Returns
    -------
    HTMLResponse
        Members page with success/error message, or redirect to login.
    """
    auth = await _get_session_user(request, db)
    if auth is None:
        return RedirectResponse(
            url=f"/ui/login?next=/ui/settings/organisations/{org_id}/members",
            status_code=302,
        )

    _, user = auth

    tid = _parse_uuid(org_id)
    if tid is None:
        return _render(
            request,
            "settings/organisation_members.html",
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
            "settings/organisation_members.html",
            {
                "user": user,
                "section": "organisations",
                "error": "Organisation not found.",
            },
        )

    membership, tenant = result

    async def _ctx(
        *, error: str | None = None, success: str | None = None
    ) -> dict[str, Any]:
        members = await _list_members(db, tid)
        return {
            "user": user,
            "section": "organisations",
            "org": {
                "id": str(tenant.id),
                "slug": tenant.slug,
                "display_name": tenant.display_name,
            },
            "members": members,
            "role": membership.role,
            "roles": _MEMBER_ROLES,
            "error": error,
            "success": success,
        }

    if membership.role not in ("owner", "admin"):
        return _render(
            request,
            "settings/organisation_members.html",
            await _ctx(error="You do not have permission to manage members."),
        )

    if action == "add":
        return await _member_add(request, db, tid, email, member_role, _ctx)
    elif action == "remove":
        return await _member_remove(request, db, tid, member_id, user, _ctx)
    elif action == "update_role":
        return await _member_update_role(
            request, db, tid, member_id, member_role, user, _ctx
        )

    return _render(
        request,
        "settings/organisation_members.html",
        await _ctx(error="Unknown action."),
    )


async def _member_add(
    request: Request,
    db: Any,
    tenant_id: uuid_mod.UUID,
    email: str,
    role: str,
    ctx_fn: Any,
) -> Any:
    """Add a member by email.

    Parameters
    ----------
    request : Request
        The HTTP request.
    db : AsyncSession
        Database session.
    tenant_id : uuid.UUID
        Tenant to add the member to.
    email : str
        Email of the user to add.
    role : str
        Role to assign.
    ctx_fn : callable
        Async function to build template context.

    Returns
    -------
    Any
        Rendered template response.
    """
    email = email.strip().lower()
    if not email:
        return _render(
            request,
            "settings/organisation_members.html",
            await ctx_fn(error="Please enter an email address."),
        )

    if role not in _MEMBER_ROLES:
        return _render(
            request,
            "settings/organisation_members.html",
            await ctx_fn(error=f"Invalid role: {role}"),
        )

    # Find user by email
    email_result = await db.execute(select(UserEmail).where(UserEmail.email == email))
    user_email = email_result.scalar_one_or_none()
    if user_email is None:
        return _render(
            request,
            "settings/organisation_members.html",
            await ctx_fn(error=f"No user found with email {email}."),
        )

    # Check if already a member
    existing = await db.execute(
        select(TenantMember).where(
            TenantMember.tenant_id == tenant_id,
            TenantMember.user_id == user_email.user_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        return _render(
            request,
            "settings/organisation_members.html",
            await ctx_fn(error="User is already a member."),
        )

    member = TenantMember(
        tenant_id=tenant_id,
        user_id=user_email.user_id,
        role=role,
        joined_at=datetime.now(timezone.utc),
    )
    db.add(member)
    await db.flush()

    return _render(
        request,
        "settings/organisation_members.html",
        await ctx_fn(success=f"Member {email} added successfully."),
    )


async def _member_remove(
    request: Request,
    db: Any,
    tenant_id: uuid_mod.UUID,
    member_id: str,
    current_user: Any,
    ctx_fn: Any,
) -> Any:
    """Remove a member from the organisation.

    Parameters
    ----------
    request : Request
        The HTTP request.
    db : AsyncSession
        Database session.
    tenant_id : uuid.UUID
        Tenant to remove from.
    member_id : str
        UUID of the member to remove.
    current_user : User
        The currently authenticated user.
    ctx_fn : callable
        Async function to build template context.

    Returns
    -------
    Any
        Rendered template response.
    """
    mid = _parse_uuid(member_id)
    if mid is None:
        return _render(
            request,
            "settings/organisation_members.html",
            await ctx_fn(error="Invalid member ID."),
        )

    result = await db.execute(
        select(TenantMember).where(
            TenantMember.id == mid, TenantMember.tenant_id == tenant_id
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        return _render(
            request,
            "settings/organisation_members.html",
            await ctx_fn(error="Member not found."),
        )

    if member.user_id == current_user.id:
        return _render(
            request,
            "settings/organisation_members.html",
            await ctx_fn(error="You cannot remove yourself."),
        )

    await db.delete(member)
    await db.flush()

    return _render(
        request,
        "settings/organisation_members.html",
        await ctx_fn(success="Member removed."),
    )


async def _member_update_role(
    request: Request,
    db: Any,
    tenant_id: uuid_mod.UUID,
    member_id: str,
    new_role: str,
    current_user: Any,
    ctx_fn: Any,
) -> Any:
    """Update a member's role.

    Parameters
    ----------
    request : Request
        The HTTP request.
    db : AsyncSession
        Database session.
    tenant_id : uuid.UUID
        Tenant context.
    member_id : str
        UUID of the member to update.
    new_role : str
        New role to assign.
    current_user : User
        The currently authenticated user.
    ctx_fn : callable
        Async function to build template context.

    Returns
    -------
    Any
        Rendered template response.
    """
    if new_role not in _MEMBER_ROLES:
        return _render(
            request,
            "settings/organisation_members.html",
            await ctx_fn(error=f"Invalid role: {new_role}"),
        )

    mid = _parse_uuid(member_id)
    if mid is None:
        return _render(
            request,
            "settings/organisation_members.html",
            await ctx_fn(error="Invalid member ID."),
        )

    result = await db.execute(
        select(TenantMember).where(
            TenantMember.id == mid, TenantMember.tenant_id == tenant_id
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        return _render(
            request,
            "settings/organisation_members.html",
            await ctx_fn(error="Member not found."),
        )

    if member.user_id == current_user.id:
        return _render(
            request,
            "settings/organisation_members.html",
            await ctx_fn(error="You cannot change your own role."),
        )

    member.role = new_role
    await db.flush()

    return _render(
        request,
        "settings/organisation_members.html",
        await ctx_fn(success=f"Role updated to {new_role}."),
    )


# ---------------------------------------------------------------------------
# Role management (CRUD + scope assignment)
# ---------------------------------------------------------------------------


@router.get("/organisations/{org_id}/roles", response_class=HTMLResponse)
async def settings_organisation_roles(
    request: Request, org_id: str, db: DbSession
) -> Any:
    """Render the role management page.

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
        Roles page, or redirect to login.
    """
    auth = await _get_session_user(request, db)
    if auth is None:
        return RedirectResponse(
            url=f"/ui/login?next=/ui/settings/organisations/{org_id}/roles",
            status_code=302,
        )

    _, user = auth

    tid = _parse_uuid(org_id)
    if tid is None:
        return _render(
            request,
            "settings/organisation_roles.html",
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
            "settings/organisation_roles.html",
            {
                "user": user,
                "section": "organisations",
                "error": "Organisation not found.",
            },
        )

    membership, tenant = result

    roles_stmt = (
        select(TenantCustomRole)
        .where(TenantCustomRole.tenant_id == tid)
        .order_by(TenantCustomRole.name)
    )
    roles_result = await db.execute(roles_stmt)
    roles = [
        {
            "id": str(r.id),
            "name": r.name,
            "permissions": r.permissions,
        }
        for r in roles_result.scalars().all()
    ]

    return _render(
        request,
        "settings/organisation_roles.html",
        {
            "user": user,
            "section": "organisations",
            "org": {
                "id": str(tenant.id),
                "slug": tenant.slug,
                "display_name": tenant.display_name,
            },
            "roles": roles,
            "role": membership.role,
            "error": None,
            "success": None,
        },
    )


@router.post("/organisations/{org_id}/roles", response_class=HTMLResponse)
async def settings_organisation_roles_action(
    request: Request,
    org_id: str,
    db: DbSession,
    action: str = Form(...),
    role_name: str = Form(""),
    permissions: str = Form(""),
    role_id: str = Form(""),
) -> Any:
    """Handle role management actions (create, update, delete).

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    org_id : str
        UUID of the organisation.
    db : DbSession
        Database session.
    action : str
        Action to perform: ``create``, ``update``, or ``delete``.
    role_name : str
        Name for the role (create/update).
    permissions : str
        Space-separated permission strings (create/update).
    role_id : str
        UUID of the role (update/delete).

    Returns
    -------
    HTMLResponse
        Roles page with success/error message, or redirect to login.
    """
    auth = await _get_session_user(request, db)
    if auth is None:
        return RedirectResponse(
            url=f"/ui/login?next=/ui/settings/organisations/{org_id}/roles",
            status_code=302,
        )

    _, user = auth

    tid = _parse_uuid(org_id)
    if tid is None:
        return _render(
            request,
            "settings/organisation_roles.html",
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
            "settings/organisation_roles.html",
            {
                "user": user,
                "section": "organisations",
                "error": "Organisation not found.",
            },
        )

    membership, tenant = result

    async def _ctx(
        *, error: str | None = None, success: str | None = None
    ) -> dict[str, Any]:
        roles_stmt = (
            select(TenantCustomRole)
            .where(TenantCustomRole.tenant_id == tid)
            .order_by(TenantCustomRole.name)
        )
        roles_result = await db.execute(roles_stmt)
        roles = [
            {"id": str(r.id), "name": r.name, "permissions": r.permissions}
            for r in roles_result.scalars().all()
        ]
        return {
            "user": user,
            "section": "organisations",
            "org": {
                "id": str(tenant.id),
                "slug": tenant.slug,
                "display_name": tenant.display_name,
            },
            "roles": roles,
            "role": membership.role,
            "error": error,
            "success": success,
        }

    if membership.role not in ("owner", "admin"):
        return _render(
            request,
            "settings/organisation_roles.html",
            await _ctx(error="You do not have permission to manage roles."),
        )

    perms_list = [p.strip() for p in permissions.split() if p.strip()]

    if action == "create":
        name = role_name.strip()
        if not name:
            return _render(
                request,
                "settings/organisation_roles.html",
                await _ctx(error="Role name is required."),
            )
        existing = await db.execute(
            select(TenantCustomRole).where(
                TenantCustomRole.tenant_id == tid,
                TenantCustomRole.name == name,
            )
        )
        if existing.scalar_one_or_none() is not None:
            return _render(
                request,
                "settings/organisation_roles.html",
                await _ctx(error=f"Role '{name}' already exists."),
            )
        role_obj = TenantCustomRole(
            tenant_id=tid,
            name=name,
            permissions=perms_list,
        )
        db.add(role_obj)
        await db.flush()
        return _render(
            request,
            "settings/organisation_roles.html",
            await _ctx(success=f"Role '{name}' created."),
        )

    elif action == "update":
        rid = _parse_uuid(role_id)
        if rid is None:
            return _render(
                request,
                "settings/organisation_roles.html",
                await _ctx(error="Invalid role ID."),
            )
        update_result = await db.execute(
            select(TenantCustomRole).where(
                TenantCustomRole.id == rid, TenantCustomRole.tenant_id == tid
            )
        )
        update_role = update_result.scalar_one_or_none()
        if update_role is None:
            return _render(
                request,
                "settings/organisation_roles.html",
                await _ctx(error="Role not found."),
            )
        if role_name.strip():
            update_role.name = role_name.strip()
        update_role.permissions = perms_list
        await db.flush()
        return _render(
            request,
            "settings/organisation_roles.html",
            await _ctx(success=f"Role '{update_role.name}' updated."),
        )

    elif action == "delete":
        rid = _parse_uuid(role_id)
        if rid is None:
            return _render(
                request,
                "settings/organisation_roles.html",
                await _ctx(error="Invalid role ID."),
            )
        delete_result = await db.execute(
            select(TenantCustomRole).where(
                TenantCustomRole.id == rid, TenantCustomRole.tenant_id == tid
            )
        )
        delete_role = delete_result.scalar_one_or_none()
        if delete_role is None:
            return _render(
                request,
                "settings/organisation_roles.html",
                await _ctx(error="Role not found."),
            )
        await db.delete(delete_role)
        await db.flush()
        return _render(
            request,
            "settings/organisation_roles.html",
            await _ctx(success="Role deleted."),
        )

    return _render(
        request,
        "settings/organisation_roles.html",
        await _ctx(error="Unknown action."),
    )


# ---------------------------------------------------------------------------
# IdP management (CRUD + toggle)
# ---------------------------------------------------------------------------

#: Valid identity provider types.
_IDP_TYPES = [t.value for t in IdentityProviderType]


@router.get("/organisations/{org_id}/idps", response_class=HTMLResponse)
async def settings_organisation_idps(
    request: Request, org_id: str, db: DbSession
) -> Any:
    """Render the identity provider management page.

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
        IdP page, or redirect to login.
    """
    auth = await _get_session_user(request, db)
    if auth is None:
        return RedirectResponse(
            url=f"/ui/login?next=/ui/settings/organisations/{org_id}/idps",
            status_code=302,
        )

    _, user = auth

    tid = _parse_uuid(org_id)
    if tid is None:
        return _render(
            request,
            "settings/organisation_idps.html",
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
            "settings/organisation_idps.html",
            {
                "user": user,
                "section": "organisations",
                "error": "Organisation not found.",
            },
        )

    membership, tenant = result

    idps_stmt = (
        select(IdentityProvider)
        .where(IdentityProvider.tenant_id == tid)
        .order_by(IdentityProvider.display_order, IdentityProvider.name)
    )
    idps_result = await db.execute(idps_stmt)
    idps = [
        {
            "id": str(idp.id),
            "name": idp.name,
            "provider_type": idp.provider_type.value,
            "client_id": idp.client_id,
            "is_active": idp.is_active,
        }
        for idp in idps_result.scalars().all()
    ]

    return _render(
        request,
        "settings/organisation_idps.html",
        {
            "user": user,
            "section": "organisations",
            "org": {
                "id": str(tenant.id),
                "slug": tenant.slug,
                "display_name": tenant.display_name,
            },
            "idps": idps,
            "provider_types": _IDP_TYPES,
            "role": membership.role,
            "error": None,
            "success": None,
        },
    )


@router.post("/organisations/{org_id}/idps", response_class=HTMLResponse)
async def settings_organisation_idps_action(
    request: Request,
    org_id: str,
    db: DbSession,
    action: str = Form(...),
    idp_name: str = Form(""),
    provider_type: str = Form("oidc"),
    client_id: str = Form(""),
    discovery_url: str = Form(""),
    idp_id: str = Form(""),
) -> Any:
    """Handle identity provider management actions (create, toggle, delete).

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    org_id : str
        UUID of the organisation.
    db : DbSession
        Database session.
    action : str
        Action to perform: ``create``, ``toggle``, or ``delete``.
    idp_name : str
        Name for the IdP (create).
    provider_type : str
        Provider type string (create).
    client_id : str
        OAuth2 client ID (create).
    discovery_url : str
        OIDC discovery URL (create, optional).
    idp_id : str
        UUID of the IdP (toggle/delete).

    Returns
    -------
    HTMLResponse
        IdP page with success/error message, or redirect to login.
    """
    auth = await _get_session_user(request, db)
    if auth is None:
        return RedirectResponse(
            url=f"/ui/login?next=/ui/settings/organisations/{org_id}/idps",
            status_code=302,
        )

    _, user = auth

    tid = _parse_uuid(org_id)
    if tid is None:
        return _render(
            request,
            "settings/organisation_idps.html",
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
            "settings/organisation_idps.html",
            {
                "user": user,
                "section": "organisations",
                "error": "Organisation not found.",
            },
        )

    membership, tenant = result

    async def _ctx(
        *, error: str | None = None, success: str | None = None
    ) -> dict[str, Any]:
        idps_stmt = (
            select(IdentityProvider)
            .where(IdentityProvider.tenant_id == tid)
            .order_by(IdentityProvider.display_order, IdentityProvider.name)
        )
        idps_result = await db.execute(idps_stmt)
        idps = [
            {
                "id": str(idp.id),
                "name": idp.name,
                "provider_type": idp.provider_type.value,
                "client_id": idp.client_id,
                "is_active": idp.is_active,
            }
            for idp in idps_result.scalars().all()
        ]
        return {
            "user": user,
            "section": "organisations",
            "org": {
                "id": str(tenant.id),
                "slug": tenant.slug,
                "display_name": tenant.display_name,
            },
            "idps": idps,
            "provider_types": _IDP_TYPES,
            "role": membership.role,
            "error": error,
            "success": success,
        }

    if membership.role not in ("owner", "admin"):
        return _render(
            request,
            "settings/organisation_idps.html",
            await _ctx(
                error="You do not have permission to manage identity providers."
            ),
        )

    if action == "create":
        name = idp_name.strip()
        if not name:
            return _render(
                request,
                "settings/organisation_idps.html",
                await _ctx(error="Provider name is required."),
            )
        if provider_type not in _IDP_TYPES:
            return _render(
                request,
                "settings/organisation_idps.html",
                await _ctx(error=f"Invalid provider type: {provider_type}"),
            )
        cid = client_id.strip()
        if not cid:
            return _render(
                request,
                "settings/organisation_idps.html",
                await _ctx(error="Client ID is required."),
            )
        idp_obj = IdentityProvider(
            tenant_id=tid,
            name=name,
            provider_type=IdentityProviderType(provider_type),
            client_id=cid,
            discovery_url=discovery_url.strip() or None,
        )
        db.add(idp_obj)
        await db.flush()
        return _render(
            request,
            "settings/organisation_idps.html",
            await _ctx(success=f"Identity provider '{name}' created."),
        )

    elif action == "toggle":
        iid = _parse_uuid(idp_id)
        if iid is None:
            return _render(
                request,
                "settings/organisation_idps.html",
                await _ctx(error="Invalid provider ID."),
            )
        toggle_result = await db.execute(
            select(IdentityProvider).where(
                IdentityProvider.id == iid, IdentityProvider.tenant_id == tid
            )
        )
        toggle_idp = toggle_result.scalar_one_or_none()
        if toggle_idp is None:
            return _render(
                request,
                "settings/organisation_idps.html",
                await _ctx(error="Provider not found."),
            )
        toggle_idp.is_active = not toggle_idp.is_active
        await db.flush()
        state = "enabled" if toggle_idp.is_active else "disabled"
        return _render(
            request,
            "settings/organisation_idps.html",
            await _ctx(success=f"Provider '{toggle_idp.name}' {state}."),
        )

    elif action == "delete":
        iid = _parse_uuid(idp_id)
        if iid is None:
            return _render(
                request,
                "settings/organisation_idps.html",
                await _ctx(error="Invalid provider ID."),
            )
        delete_result = await db.execute(
            select(IdentityProvider).where(
                IdentityProvider.id == iid, IdentityProvider.tenant_id == tid
            )
        )
        delete_idp = delete_result.scalar_one_or_none()
        if delete_idp is None:
            return _render(
                request,
                "settings/organisation_idps.html",
                await _ctx(error="Provider not found."),
            )
        await db.delete(delete_idp)
        await db.flush()
        return _render(
            request,
            "settings/organisation_idps.html",
            await _ctx(success="Provider deleted."),
        )

    return _render(
        request,
        "settings/organisation_idps.html",
        await _ctx(error="Unknown action."),
    )


# ---------------------------------------------------------------------------
# Branding customization
# ---------------------------------------------------------------------------

#: Regex for CSS hex color (3 or 6 digit).
_HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}){1,2}$")

#: Branding color fields that can be updated.
_BRANDING_COLOR_FIELDS = (
    "primary_color",
    "secondary_color",
    "accent_color",
    "background_color",
    "surface_color",
    "text_color",
    "text_muted_color",
    "error_color",
    "success_color",
    "border_color",
    "warning_color",
    "info_color",
)


def _branding_to_dict(branding: TenantBranding | None) -> dict[str, Any]:
    """Convert a TenantBranding to a template-friendly dict.

    Parameters
    ----------
    branding : TenantBranding or None
        The branding object.

    Returns
    -------
    dict
        Branding fields as a dict, or empty defaults.
    """
    if branding is None:
        return {
            "logo_url": "",
            "favicon_url": "",
            "primary_color": "",
            "font_family": "",
            "custom_css": "",
            "show_powered_by": True,
        }
    return {
        "logo_url": branding.logo_url or "",
        "favicon_url": branding.favicon_url or "",
        "primary_color": branding.primary_color or "",
        "secondary_color": branding.secondary_color or "",
        "accent_color": branding.accent_color or "",
        "background_color": branding.background_color or "",
        "font_family": branding.font_family or "",
        "custom_css": branding.custom_css or "",
        "show_powered_by": branding.show_powered_by,
    }


@router.get("/organisations/{org_id}/branding", response_class=HTMLResponse)
async def settings_organisation_branding(
    request: Request, org_id: str, db: DbSession
) -> Any:
    """Render the branding customization page.

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
        Branding page, or redirect to login.
    """
    auth = await _get_session_user(request, db)
    if auth is None:
        return RedirectResponse(
            url=f"/ui/login?next=/ui/settings/organisations/{org_id}/branding",
            status_code=302,
        )

    _, user = auth

    tid = _parse_uuid(org_id)
    if tid is None:
        return _render(
            request,
            "settings/organisation_branding.html",
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
            "settings/organisation_branding.html",
            {
                "user": user,
                "section": "organisations",
                "error": "Organisation not found.",
            },
        )

    membership, tenant = result

    branding_result = await db.execute(
        select(TenantBranding).where(TenantBranding.tenant_id == tid)
    )
    branding = branding_result.scalar_one_or_none()

    return _render(
        request,
        "settings/organisation_branding.html",
        {
            "user": user,
            "section": "organisations",
            "org": {
                "id": str(tenant.id),
                "slug": tenant.slug,
                "display_name": tenant.display_name,
            },
            "branding": _branding_to_dict(branding),
            "role": membership.role,
            "error": None,
            "success": None,
        },
    )


@router.post("/organisations/{org_id}/branding", response_class=HTMLResponse)
async def settings_organisation_branding_update(
    request: Request,
    org_id: str,
    db: DbSession,
    logo_url: str = Form(""),
    favicon_url: str = Form(""),
    primary_color: str = Form(""),
    secondary_color: str = Form(""),
    accent_color: str = Form(""),
    background_color: str = Form(""),
    font_family: str = Form(""),
    custom_css: str = Form(""),
    show_powered_by: str = Form(""),
) -> Any:
    """Handle branding update form submission.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    org_id : str
        UUID of the organisation.
    db : DbSession
        Database session.
    logo_url : str
        Logo URL.
    favicon_url : str
        Favicon URL.
    primary_color : str
        Primary brand color (hex).
    secondary_color : str
        Secondary brand color (hex).
    accent_color : str
        Accent color (hex).
    background_color : str
        Background color (hex).
    font_family : str
        CSS font family.
    custom_css : str
        Custom CSS.
    show_powered_by : str
        Whether to show "Powered by" footer ("on" or empty).

    Returns
    -------
    HTMLResponse
        Branding page with success/error message, or redirect to login.
    """
    auth = await _get_session_user(request, db)
    if auth is None:
        return RedirectResponse(
            url=f"/ui/login?next=/ui/settings/organisations/{org_id}/branding",
            status_code=302,
        )

    _, user = auth

    tid = _parse_uuid(org_id)
    if tid is None:
        return _render(
            request,
            "settings/organisation_branding.html",
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
            "settings/organisation_branding.html",
            {
                "user": user,
                "section": "organisations",
                "error": "Organisation not found.",
            },
        )

    membership, tenant = result

    branding_result = await db.execute(
        select(TenantBranding).where(TenantBranding.tenant_id == tid)
    )
    branding = branding_result.scalar_one_or_none()

    def _ctx(*, error: str | None = None, success: str | None = None) -> dict[str, Any]:
        return {
            "user": user,
            "section": "organisations",
            "org": {
                "id": str(tenant.id),
                "slug": tenant.slug,
                "display_name": tenant.display_name,
            },
            "branding": _branding_to_dict(branding),
            "role": membership.role,
            "error": error,
            "success": success,
        }

    if membership.role not in ("owner", "admin"):
        return _render(
            request,
            "settings/organisation_branding.html",
            _ctx(error="You do not have permission to update branding."),
        )

    # Validate color fields
    for color_val, color_name in [
        (primary_color, "primary"),
        (secondary_color, "secondary"),
        (accent_color, "accent"),
        (background_color, "background"),
    ]:
        if color_val.strip() and not _HEX_COLOR_RE.match(color_val.strip()):
            return _render(
                request,
                "settings/organisation_branding.html",
                _ctx(
                    error=f"Invalid {color_name} color. Use hex format (#RGB or #RRGGBB)."
                ),
            )

    if branding is None:
        branding = TenantBranding(tenant_id=tid)
        db.add(branding)

    branding.logo_url = logo_url.strip() or None
    branding.favicon_url = favicon_url.strip() or None
    branding.primary_color = primary_color.strip() or None
    branding.secondary_color = secondary_color.strip() or None
    branding.accent_color = accent_color.strip() or None
    branding.background_color = background_color.strip() or None
    branding.font_family = font_family.strip() or None
    branding.custom_css = custom_css.strip() or None
    branding.show_powered_by = show_powered_by == "on"
    await db.flush()

    return _render(
        request,
        "settings/organisation_branding.html",
        _ctx(success="Branding updated successfully."),
    )


# ---------------------------------------------------------------------------
# Trust policies
# ---------------------------------------------------------------------------


@router.get("/organisations/{org_id}/trust", response_class=HTMLResponse)
async def settings_organisation_trust(
    request: Request, org_id: str, db: DbSession
) -> Any:
    """Render the trust policies page.

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
        Trust policies page, or redirect to login.
    """
    auth = await _get_session_user(request, db)
    if auth is None:
        return RedirectResponse(
            url=f"/ui/login?next=/ui/settings/organisations/{org_id}/trust",
            status_code=302,
        )

    _, user = auth

    tid = _parse_uuid(org_id)
    if tid is None:
        return _render(
            request,
            "settings/organisation_trust.html",
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
            "settings/organisation_trust.html",
            {
                "user": user,
                "section": "organisations",
                "error": "Organisation not found.",
            },
        )

    membership, tenant = result

    sources_stmt = (
        select(TenantTrustedSource)
        .where(TenantTrustedSource.tenant_id == tid)
        .options(selectinload(TenantTrustedSource.trusted_tenant))
        .order_by(TenantTrustedSource.created_at)
    )
    sources_result = await db.execute(sources_stmt)
    sources = [
        {
            "id": str(s.id),
            "trusted_tenant_slug": s.trusted_tenant.slug,
            "trusted_tenant_name": s.trusted_tenant.display_name,
            "description": s.description or "",
        }
        for s in sources_result.scalars().all()
    ]

    return _render(
        request,
        "settings/organisation_trust.html",
        {
            "user": user,
            "section": "organisations",
            "org": {
                "id": str(tenant.id),
                "slug": tenant.slug,
                "display_name": tenant.display_name,
            },
            "trust_mode": _trust_mode_str(tenant),
            "trust_modes": [m.value for m in TenantTrustMode],
            "sources": sources,
            "role": membership.role,
            "error": None,
            "success": None,
        },
    )


@router.post("/organisations/{org_id}/trust", response_class=HTMLResponse)
async def settings_organisation_trust_action(
    request: Request,
    org_id: str,
    db: DbSession,
    action: str = Form(...),
    trust_mode: str = Form(""),
    trusted_slug: str = Form(""),
    description: str = Form(""),
    source_id: str = Form(""),
) -> Any:
    """Handle trust policy actions (update mode, add source, remove source).

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    org_id : str
        UUID of the organisation.
    db : DbSession
        Database session.
    action : str
        Action: ``update_mode``, ``add_source``, or ``remove_source``.
    trust_mode : str
        New trust mode value (for update_mode).
    trusted_slug : str
        Slug of tenant to trust (for add_source).
    description : str
        Description of the trust relationship (for add_source).
    source_id : str
        UUID of the source to remove (for remove_source).

    Returns
    -------
    HTMLResponse
        Trust page with success/error message, or redirect to login.
    """
    auth = await _get_session_user(request, db)
    if auth is None:
        return RedirectResponse(
            url=f"/ui/login?next=/ui/settings/organisations/{org_id}/trust",
            status_code=302,
        )

    _, user = auth

    tid = _parse_uuid(org_id)
    if tid is None:
        return _render(
            request,
            "settings/organisation_trust.html",
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
            "settings/organisation_trust.html",
            {
                "user": user,
                "section": "organisations",
                "error": "Organisation not found.",
            },
        )

    membership, tenant = result

    async def _ctx(
        *, error: str | None = None, success: str | None = None
    ) -> dict[str, Any]:
        sources_stmt = (
            select(TenantTrustedSource)
            .where(TenantTrustedSource.tenant_id == tid)
            .options(selectinload(TenantTrustedSource.trusted_tenant))
            .order_by(TenantTrustedSource.created_at)
        )
        sources_result = await db.execute(sources_stmt)
        sources = [
            {
                "id": str(s.id),
                "trusted_tenant_slug": s.trusted_tenant.slug,
                "trusted_tenant_name": s.trusted_tenant.display_name,
                "description": s.description or "",
            }
            for s in sources_result.scalars().all()
        ]
        return {
            "user": user,
            "section": "organisations",
            "org": {
                "id": str(tenant.id),
                "slug": tenant.slug,
                "display_name": tenant.display_name,
            },
            "trust_mode": _trust_mode_str(tenant),
            "trust_modes": [m.value for m in TenantTrustMode],
            "sources": sources,
            "role": membership.role,
            "error": error,
            "success": success,
        }

    if membership.role not in ("owner", "admin"):
        return _render(
            request,
            "settings/organisation_trust.html",
            await _ctx(error="You do not have permission to manage trust policies."),
        )

    if action == "update_mode":
        try:
            new_mode = TenantTrustMode(trust_mode)
        except ValueError:
            return _render(
                request,
                "settings/organisation_trust.html",
                await _ctx(error=f"Invalid trust mode: {trust_mode}"),
            )
        tenant.trust_mode = new_mode
        await db.flush()
        return _render(
            request,
            "settings/organisation_trust.html",
            await _ctx(success=f"Trust mode updated to {new_mode.value}."),
        )

    elif action == "add_source":
        slug = trusted_slug.strip()
        if not slug:
            return _render(
                request,
                "settings/organisation_trust.html",
                await _ctx(error="Trusted organisation slug is required."),
            )
        trusted_result = await db.execute(select(Tenant).where(Tenant.slug == slug))
        trusted_tenant = trusted_result.scalar_one_or_none()
        if trusted_tenant is None:
            return _render(
                request,
                "settings/organisation_trust.html",
                await _ctx(error=f"Organisation '{slug}' not found."),
            )
        if trusted_tenant.id == tid:
            return _render(
                request,
                "settings/organisation_trust.html",
                await _ctx(error="Cannot trust your own organisation."),
            )
        # Check duplicate
        dup_result = await db.execute(
            select(TenantTrustedSource).where(
                TenantTrustedSource.tenant_id == tid,
                TenantTrustedSource.trusted_tenant_id == trusted_tenant.id,
            )
        )
        if dup_result.scalar_one_or_none() is not None:
            return _render(
                request,
                "settings/organisation_trust.html",
                await _ctx(error=f"Organisation '{slug}' is already trusted."),
            )
        source = TenantTrustedSource(
            tenant_id=tid,
            trusted_tenant_id=trusted_tenant.id,
            description=description.strip() or None,
        )
        db.add(source)
        await db.flush()
        return _render(
            request,
            "settings/organisation_trust.html",
            await _ctx(success=f"Trusted source '{slug}' added."),
        )

    elif action == "remove_source":
        sid = _parse_uuid(source_id)
        if sid is None:
            return _render(
                request,
                "settings/organisation_trust.html",
                await _ctx(error="Invalid source ID."),
            )
        source_result = await db.execute(
            select(TenantTrustedSource).where(
                TenantTrustedSource.id == sid, TenantTrustedSource.tenant_id == tid
            )
        )
        source_obj = source_result.scalar_one_or_none()
        if source_obj is None:
            return _render(
                request,
                "settings/organisation_trust.html",
                await _ctx(error="Trusted source not found."),
            )
        await db.delete(source_obj)
        await db.flush()
        return _render(
            request,
            "settings/organisation_trust.html",
            await _ctx(success="Trusted source removed."),
        )

    return _render(
        request,
        "settings/organisation_trust.html",
        await _ctx(error="Unknown action."),
    )


# ---------------------------------------------------------------------------
# Email template management
# ---------------------------------------------------------------------------


@router.get("/organisations/{org_id}/templates", response_class=HTMLResponse)
async def settings_organisation_templates(
    request: Request, org_id: str, db: DbSession
) -> Any:
    """Render the email template management page.

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
        Templates page, or redirect to login.
    """
    auth = await _get_session_user(request, db)
    if auth is None:
        return RedirectResponse(
            url=f"/ui/login?next=/ui/settings/organisations/{org_id}/templates",
            status_code=302,
        )

    _, user = auth

    tid = _parse_uuid(org_id)
    if tid is None:
        return _render(
            request,
            "settings/organisation_templates.html",
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
            "settings/organisation_templates.html",
            {
                "user": user,
                "section": "organisations",
                "error": "Organisation not found.",
            },
        )

    membership, tenant = result

    tmpl_stmt = (
        select(TenantTemplate)
        .where(TenantTemplate.tenant_id == tid)
        .order_by(TenantTemplate.template_name)
    )
    tmpl_result = await db.execute(tmpl_stmt)
    templates_list = [
        {
            "id": str(t.id),
            "template_name": t.template_name,
            "description": t.description or "",
            "is_active": t.is_active,
        }
        for t in tmpl_result.scalars().all()
    ]

    return _render(
        request,
        "settings/organisation_templates.html",
        {
            "user": user,
            "section": "organisations",
            "org": {
                "id": str(tenant.id),
                "slug": tenant.slug,
                "display_name": tenant.display_name,
            },
            "templates": templates_list,
            "role": membership.role,
            "error": None,
            "success": None,
        },
    )


@router.post("/organisations/{org_id}/templates", response_class=HTMLResponse)
async def settings_organisation_templates_action(
    request: Request,
    org_id: str,
    db: DbSession,
    action: str = Form(...),
    template_name: str = Form(""),
    content: str = Form(""),
    description: str = Form(""),
    template_id: str = Form(""),
) -> Any:
    """Handle template management actions (create, update, toggle, delete).

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    org_id : str
        UUID of the organisation.
    db : DbSession
        Database session.
    action : str
        Action: ``create``, ``update``, ``toggle``, or ``delete``.
    template_name : str
        Template path (for create).
    content : str
        Template content (for create/update).
    description : str
        Description (for create/update).
    template_id : str
        UUID of the template (for update/toggle/delete).

    Returns
    -------
    HTMLResponse
        Templates page with success/error message, or redirect to login.
    """
    auth = await _get_session_user(request, db)
    if auth is None:
        return RedirectResponse(
            url=f"/ui/login?next=/ui/settings/organisations/{org_id}/templates",
            status_code=302,
        )

    _, user = auth

    tid = _parse_uuid(org_id)
    if tid is None:
        return _render(
            request,
            "settings/organisation_templates.html",
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
            "settings/organisation_templates.html",
            {
                "user": user,
                "section": "organisations",
                "error": "Organisation not found.",
            },
        )

    membership, tenant = result

    async def _ctx(
        *, error: str | None = None, success: str | None = None
    ) -> dict[str, Any]:
        tmpl_stmt = (
            select(TenantTemplate)
            .where(TenantTemplate.tenant_id == tid)
            .order_by(TenantTemplate.template_name)
        )
        tmpl_result = await db.execute(tmpl_stmt)
        templates_list = [
            {
                "id": str(t.id),
                "template_name": t.template_name,
                "description": t.description or "",
                "is_active": t.is_active,
            }
            for t in tmpl_result.scalars().all()
        ]
        return {
            "user": user,
            "section": "organisations",
            "org": {
                "id": str(tenant.id),
                "slug": tenant.slug,
                "display_name": tenant.display_name,
            },
            "templates": templates_list,
            "role": membership.role,
            "error": error,
            "success": success,
        }

    if membership.role not in ("owner", "admin"):
        return _render(
            request,
            "settings/organisation_templates.html",
            await _ctx(error="You do not have permission to manage templates."),
        )

    if action == "create":
        name = template_name.strip()
        if not name:
            return _render(
                request,
                "settings/organisation_templates.html",
                await _ctx(error="Template name is required."),
            )
        if not content.strip():
            return _render(
                request,
                "settings/organisation_templates.html",
                await _ctx(error="Template content is required."),
            )
        # Check duplicate
        dup_result = await db.execute(
            select(TenantTemplate).where(
                TenantTemplate.tenant_id == tid,
                TenantTemplate.template_name == name,
            )
        )
        if dup_result.scalar_one_or_none() is not None:
            return _render(
                request,
                "settings/organisation_templates.html",
                await _ctx(error=f"Template '{name}' already exists."),
            )
        tmpl = TenantTemplate(
            tenant_id=tid,
            template_name=name,
            content=content.strip(),
            description=description.strip() or None,
        )
        db.add(tmpl)
        await db.flush()
        return _render(
            request,
            "settings/organisation_templates.html",
            await _ctx(success=f"Template '{name}' created."),
        )

    elif action == "update":
        tmpl_id = _parse_uuid(template_id)
        if tmpl_id is None:
            return _render(
                request,
                "settings/organisation_templates.html",
                await _ctx(error="Invalid template ID."),
            )
        update_result = await db.execute(
            select(TenantTemplate).where(
                TenantTemplate.id == tmpl_id, TenantTemplate.tenant_id == tid
            )
        )
        update_tmpl = update_result.scalar_one_or_none()
        if update_tmpl is None:
            return _render(
                request,
                "settings/organisation_templates.html",
                await _ctx(error="Template not found."),
            )
        if content.strip():
            update_tmpl.content = content.strip()
        if description.strip():
            update_tmpl.description = description.strip()
        await db.flush()
        return _render(
            request,
            "settings/organisation_templates.html",
            await _ctx(success=f"Template '{update_tmpl.template_name}' updated."),
        )

    elif action == "toggle":
        tmpl_id = _parse_uuid(template_id)
        if tmpl_id is None:
            return _render(
                request,
                "settings/organisation_templates.html",
                await _ctx(error="Invalid template ID."),
            )
        toggle_result = await db.execute(
            select(TenantTemplate).where(
                TenantTemplate.id == tmpl_id, TenantTemplate.tenant_id == tid
            )
        )
        toggle_tmpl = toggle_result.scalar_one_or_none()
        if toggle_tmpl is None:
            return _render(
                request,
                "settings/organisation_templates.html",
                await _ctx(error="Template not found."),
            )
        toggle_tmpl.is_active = not toggle_tmpl.is_active
        await db.flush()
        state = "enabled" if toggle_tmpl.is_active else "disabled"
        return _render(
            request,
            "settings/organisation_templates.html",
            await _ctx(success=f"Template '{toggle_tmpl.template_name}' {state}."),
        )

    elif action == "delete":
        tmpl_id = _parse_uuid(template_id)
        if tmpl_id is None:
            return _render(
                request,
                "settings/organisation_templates.html",
                await _ctx(error="Invalid template ID."),
            )
        delete_result = await db.execute(
            select(TenantTemplate).where(
                TenantTemplate.id == tmpl_id, TenantTemplate.tenant_id == tid
            )
        )
        delete_tmpl = delete_result.scalar_one_or_none()
        if delete_tmpl is None:
            return _render(
                request,
                "settings/organisation_templates.html",
                await _ctx(error="Template not found."),
            )
        await db.delete(delete_tmpl)
        await db.flush()
        return _render(
            request,
            "settings/organisation_templates.html",
            await _ctx(success="Template deleted."),
        )

    return _render(
        request,
        "settings/organisation_templates.html",
        await _ctx(error="Unknown action."),
    )

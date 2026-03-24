# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Admin UI routes (Jinja2/HTMX).

Dashboard and management pages for administrators.
Requires session authentication and admin scope.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from shomer.deps import DbSession
from shomer.models.access_token import AccessToken
from shomer.models.oauth2_client import OAuth2Client
from shomer.models.session import Session
from shomer.models.user import User
from shomer.models.user_email import UserEmail
from shomer.models.user_mfa import UserMFA
from shomer.services.rbac_service import RBACService
from shomer.services.session_service import SessionService

router = APIRouter(prefix="/ui/admin", tags=["admin-ui"], include_in_schema=False)


def _templates() -> Jinja2Templates:
    """Get the Jinja2 templates instance."""
    from shomer.app import templates

    return templates


def _render(request: Request, template: str, ctx: dict[str, Any] | None = None) -> Any:
    """Render a template with the given context."""
    return _templates().TemplateResponse(request, template, ctx or {})


async def _get_admin_user(request: Request, db: Any) -> Any | None:
    """Validate session and verify admin scope.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : AsyncSession
        Database session.

    Returns
    -------
    User or None
        The authenticated admin user, or None.
    """
    session_token = request.cookies.get("session_id")
    if not session_token:
        return None

    svc = SessionService(db)
    session = await svc.validate(session_token)
    if session is None:
        return None

    result = await db.execute(
        select(User)
        .where(User.id == session.user_id)
        .options(selectinload(User.emails))
    )
    user = result.scalar_one_or_none()
    if user is None:
        return None

    # Check admin scope
    rbac = RBACService(db)
    has_admin = await rbac.has_permission(user.id, "admin:dashboard:read")
    if not has_admin:
        return None

    return user


@router.get("", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: DbSession) -> Any:
    """Render the admin dashboard page.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.

    Returns
    -------
    HTMLResponse
        Dashboard page or redirect to login.
    """
    user = await _get_admin_user(request, db)
    if user is None:
        return RedirectResponse(url="/ui/login?next=/ui/admin", status_code=302)

    now = datetime.now(timezone.utc)
    last_24h = now - timedelta(hours=24)

    # Gather stats (same as API dashboard)
    total_users_r = await db.execute(select(func.count()).select_from(User))
    total_users = total_users_r.scalar() or 0

    active_users_r = await db.execute(
        select(func.count()).select_from(User).where(User.is_active == True)  # noqa: E712
    )
    active_users = active_users_r.scalar() or 0

    verified_r = await db.execute(
        select(func.count(func.distinct(UserEmail.user_id))).where(
            UserEmail.is_verified == True  # noqa: E712
        )
    )
    verified_users = verified_r.scalar() or 0

    sessions_r = await db.execute(
        select(func.count()).select_from(Session).where(Session.expires_at > now)
    )
    active_sessions = sessions_r.scalar() or 0

    clients_r = await db.execute(select(func.count()).select_from(OAuth2Client))
    total_clients = clients_r.scalar() or 0

    conf_clients_r = await db.execute(
        select(func.count())
        .select_from(OAuth2Client)
        .where(OAuth2Client.client_type == "CONFIDENTIAL")
    )
    confidential_clients = conf_clients_r.scalar() or 0

    tokens_r = await db.execute(
        select(func.count())
        .select_from(AccessToken)
        .where(AccessToken.created_at > last_24h)
    )
    tokens_24h = tokens_r.scalar() or 0

    mfa_r = await db.execute(
        select(func.count()).select_from(UserMFA).where(UserMFA.is_enabled == True)  # noqa: E712
    )
    mfa_enabled = mfa_r.scalar() or 0

    mfa_rate = round(mfa_enabled / total_users * 100, 1) if total_users > 0 else 0.0

    stats = {
        "users": {
            "total": total_users,
            "active": active_users,
            "verified": verified_users,
        },
        "sessions": {"active": active_sessions},
        "clients": {
            "total": total_clients,
            "confidential": confidential_clients,
            "public": total_clients - confidential_clients,
        },
        "tokens": {"issued_24h": tokens_24h},
        "mfa": {"enabled": mfa_enabled, "adoption_rate": mfa_rate},
    }

    return _render(
        request,
        "admin/dashboard.html",
        {"user": user, "stats": stats, "section": "dashboard"},
    )


# ---------------------------------------------------------------------------
# Users UI
# ---------------------------------------------------------------------------


@router.get("/users", response_class=HTMLResponse)
async def admin_users_list(
    request: Request,
    db: DbSession,
    q: str | None = None,
    is_active: str | None = None,
    page: int = 1,
) -> Any:
    """Render the admin users list page.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.
    q : str or None
        Search query.
    is_active : str or None
        Active filter (``"true"`` or ``"false"``).
    page : int
        Page number.

    Returns
    -------
    HTMLResponse
        Users list page or redirect to login.
    """
    user = await _get_admin_user(request, db)
    if user is None:
        return RedirectResponse(url="/ui/login?next=/ui/admin/users", status_code=302)

    from sqlalchemy import or_

    from shomer.models.user_email import UserEmail as UE

    page_size = 20
    stmt = select(User).options(selectinload(User.emails))

    if q:
        pattern = f"%{q}%"
        stmt = stmt.outerjoin(UE, User.id == UE.user_id).where(
            or_(User.username.ilike(pattern), UE.email.ilike(pattern))
        )

    if is_active == "true":
        stmt = stmt.where(User.is_active == True)  # noqa: E712
    elif is_active == "false":
        stmt = stmt.where(User.is_active == False)  # noqa: E712

    count_stmt = select(func.count()).select_from(
        stmt.with_only_columns(User.id).distinct().subquery()
    )
    count_r = await db.execute(count_stmt)
    total = count_r.scalar() or 0

    offset = (page - 1) * page_size
    stmt = (
        stmt.order_by(User.created_at.desc()).offset(offset).limit(page_size).distinct()
    )
    result = await db.execute(stmt)
    users_list = list(result.scalars().unique().all())

    items = []
    for u in users_list:
        primary_email = next(
            (e.email for e in u.emails if e.is_primary),
            u.emails[0].email if u.emails else None,
        )
        items.append(
            {
                "id": str(u.id),
                "username": u.username,
                "email": primary_email,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
        )

    return _render(
        request,
        "admin/users_list.html",
        {
            "users": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "q": q,
            "is_active": is_active,
            "section": "users",
        },
    )


@router.get("/users/new", response_class=HTMLResponse)
async def admin_user_create_form(request: Request, db: DbSession) -> Any:
    """Render the user creation form.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.

    Returns
    -------
    HTMLResponse
        User creation form or redirect to login.
    """
    user = await _get_admin_user(request, db)
    if user is None:
        return RedirectResponse(
            url="/ui/login?next=/ui/admin/users/new", status_code=302
        )

    return _render(
        request,
        "admin/user_form.html",
        {"edit": False, "section": "users", "error": None, "success": None},
    )


@router.post("/users/new", response_class=HTMLResponse)
async def admin_user_create_submit(
    request: Request,
    db: DbSession,
    email: str = Form(...),
    password: str = Form(...),
    username: str = Form(""),
    is_active: str = Form(""),
) -> Any:
    """Handle user creation form submission.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.
    email : str
        User email.
    password : str
        User password.
    username : str
        Optional username.
    is_active : str
        Checkbox value.

    Returns
    -------
    HTMLResponse
        Form with success/error or redirect.
    """
    admin = await _get_admin_user(request, db)
    if admin is None:
        return RedirectResponse(url="/ui/login", status_code=302)

    from shomer.core.security import hash_password
    from shomer.models.queries import create_user as _create_user

    # Check duplicate
    existing = await db.execute(select(UserEmail).where(UserEmail.email == email))
    if existing.scalar_one_or_none() is not None:
        return _render(
            request,
            "admin/user_form.html",
            {
                "edit": False,
                "section": "users",
                "error": "Email already registered",
                "success": None,
                "email": email,
                "username": username,
            },
        )

    pw_hash = hash_password(password)
    new_user = await _create_user(
        db, email=email, password_hash=pw_hash, username=username or None
    )
    new_user.is_active = is_active == "on"

    # Auto-verify email
    email_result = await db.execute(
        select(UserEmail).where(UserEmail.user_id == new_user.id)
    )
    for e in email_result.scalars().all():
        e.is_verified = True

    await db.flush()

    return RedirectResponse(url=f"/ui/admin/users/{new_user.id}", status_code=302)


@router.get("/users/{user_id}", response_class=HTMLResponse)
async def admin_user_detail(request: Request, user_id: str, db: DbSession) -> Any:
    """Render user detail page.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    user_id : str
        UUID of the user.
    db : DbSession
        Database session.

    Returns
    -------
    HTMLResponse
        User detail page or redirect.
    """
    admin = await _get_admin_user(request, db)
    if admin is None:
        return RedirectResponse(url="/ui/login", status_code=302)

    import uuid as _uuid

    try:
        uid = _uuid.UUID(user_id)
    except ValueError:
        return RedirectResponse(url="/ui/admin/users", status_code=302)

    result = await db.execute(
        select(User)
        .where(User.id == uid)
        .options(selectinload(User.emails), selectinload(User.profile))
    )
    target = result.scalar_one_or_none()
    if target is None:
        return RedirectResponse(url="/ui/admin/users", status_code=302)

    # Build detail data
    from shomer.models.user_role import UserRole

    now = datetime.now(timezone.utc)
    sessions_r = await db.execute(
        select(func.count())
        .select_from(Session)
        .where(Session.user_id == uid, Session.expires_at > now)
    )
    active_sessions = sessions_r.scalar() or 0

    roles_r = await db.execute(
        select(UserRole)
        .where(UserRole.user_id == uid)
        .options(selectinload(UserRole.role))
    )
    roles = [
        {"name": ur.role.name, "id": str(ur.role.id)} for ur in roles_r.scalars().all()
    ]

    profile_data = None
    if target.profile:
        p = target.profile
        profile_data = {}
        for field in (
            "name",
            "given_name",
            "family_name",
            "nickname",
            "locale",
            "zoneinfo",
        ):
            val = getattr(p, field, None)
            if val:
                profile_data[field] = val

    user_data = {
        "id": str(target.id),
        "username": target.username,
        "is_active": target.is_active,
        "emails": [
            {"email": e.email, "is_primary": e.is_primary, "is_verified": e.is_verified}
            for e in target.emails
        ],
        "profile": profile_data,
        "roles": roles,
        "active_sessions": active_sessions,
    }

    return _render(
        request,
        "admin/user_detail.html",
        {"user_data": user_data, "section": "users"},
    )


# ---------------------------------------------------------------------------
# Clients UI
# ---------------------------------------------------------------------------


@router.get("/clients", response_class=HTMLResponse)
async def admin_clients_list(request: Request, db: DbSession) -> Any:
    """Render the admin clients list page.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.

    Returns
    -------
    HTMLResponse
        Clients list page or redirect.
    """
    admin = await _get_admin_user(request, db)
    if admin is None:
        return RedirectResponse(url="/ui/login?next=/ui/admin/clients", status_code=302)

    result = await db.execute(
        select(OAuth2Client).order_by(OAuth2Client.created_at.desc())
    )
    clients = list(result.scalars().all())

    items = []
    for c in clients:
        ct = c.client_type
        ct_val = ct.value if hasattr(ct, "value") else str(ct)
        items.append(
            {
                "id": str(c.id),
                "client_id": c.client_id,
                "client_name": c.client_name,
                "client_type": ct_val,
                "is_active": c.is_active,
            }
        )

    return _render(
        request,
        "admin/clients_list.html",
        {"clients": items, "section": "clients"},
    )


@router.get("/clients/new", response_class=HTMLResponse)
async def admin_client_create_form(request: Request, db: DbSession) -> Any:
    """Render the client creation form.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.

    Returns
    -------
    HTMLResponse
        Client creation form or redirect.
    """
    admin = await _get_admin_user(request, db)
    if admin is None:
        return RedirectResponse(url="/ui/login", status_code=302)

    return _render(
        request,
        "admin/client_form.html",
        {
            "edit": False,
            "section": "clients",
            "error": None,
            "success": None,
            "new_secret": None,
        },
    )


@router.post("/clients/new", response_class=HTMLResponse)
async def admin_client_create_submit(
    request: Request,
    db: DbSession,
    client_name: str = Form(...),
    client_type: str = Form("confidential"),
    redirect_uris: str = Form(""),
    grant_types: str = Form("authorization_code"),
    scopes: str = Form("openid profile email"),
) -> Any:
    """Handle client creation form submission.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.
    client_name : str
        Client display name.
    client_type : str
        confidential or public.
    redirect_uris : str
        Newline-separated redirect URIs.
    grant_types : str
        Comma-separated grant types.
    scopes : str
        Comma-separated scopes.

    Returns
    -------
    HTMLResponse
        Form with secret or redirect.
    """
    admin = await _get_admin_user(request, db)
    if admin is None:
        return RedirectResponse(url="/ui/login", status_code=302)

    from shomer.models.oauth2_client import ClientType
    from shomer.services.oauth2_client_service import OAuth2ClientService

    try:
        ct = ClientType(client_type)
    except ValueError:
        return _render(
            request,
            "admin/client_form.html",
            {
                "edit": False,
                "section": "clients",
                "error": f"Invalid type: {client_type}",
                "success": None,
                "new_secret": None,
            },
        )

    uris = [u.strip() for u in redirect_uris.strip().splitlines() if u.strip()]
    grants = [g.strip() for g in grant_types.split(",") if g.strip()]
    scope_list = [s.strip() for s in scopes.split(",") if s.strip()]

    svc = OAuth2ClientService(db)
    client, raw_secret = await svc.create_client(
        client_name=client_name,
        client_type=ct,
        redirect_uris=uris,
        grant_types=grants,
        scopes=scope_list,
    )

    return _render(
        request,
        "admin/client_form.html",
        {
            "edit": False,
            "section": "clients",
            "error": None,
            "success": f"Client '{client_name}' created. Client ID: {client.client_id}",
            "new_secret": raw_secret,
            "client_name": client_name,
        },
    )


@router.get("/clients/{client_id}", response_class=HTMLResponse)
async def admin_client_detail(request: Request, client_id: str, db: DbSession) -> Any:
    """Render client detail page.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    client_id : str
        UUID of the client.
    db : DbSession
        Database session.

    Returns
    -------
    HTMLResponse
        Client detail page or redirect.
    """
    admin = await _get_admin_user(request, db)
    if admin is None:
        return RedirectResponse(url="/ui/login", status_code=302)

    import uuid as _uuid

    try:
        cid = _uuid.UUID(client_id)
    except ValueError:
        return RedirectResponse(url="/ui/admin/clients", status_code=302)

    result = await db.execute(select(OAuth2Client).where(OAuth2Client.id == cid))
    client = result.scalar_one_or_none()
    if client is None:
        return RedirectResponse(url="/ui/admin/clients", status_code=302)

    ct = client.client_type
    am = client.token_endpoint_auth_method
    client_data = {
        "id": str(client.id),
        "client_id": client.client_id,
        "client_name": client.client_name,
        "client_type": ct.value if hasattr(ct, "value") else str(ct),
        "token_endpoint_auth_method": am.value if hasattr(am, "value") else str(am),
        "redirect_uris": client.redirect_uris,
        "grant_types": client.grant_types,
        "scopes": client.scopes,
        "is_active": client.is_active,
    }

    return _render(
        request,
        "admin/client_detail.html",
        {
            "client_data": client_data,
            "section": "clients",
            "success": None,
            "new_secret": None,
        },
    )


@router.post("/clients/{client_id}/rotate-secret", response_class=HTMLResponse)
async def admin_client_rotate_secret(
    request: Request, client_id: str, db: DbSession
) -> Any:
    """Handle secret rotation from the client detail page.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    client_id : str
        UUID of the client.
    db : DbSession
        Database session.

    Returns
    -------
    HTMLResponse
        Client detail page with new secret.
    """
    admin = await _get_admin_user(request, db)
    if admin is None:
        return RedirectResponse(url="/ui/login", status_code=302)

    import uuid as _uuid

    try:
        cid = _uuid.UUID(client_id)
    except ValueError:
        return RedirectResponse(url="/ui/admin/clients", status_code=302)

    result = await db.execute(select(OAuth2Client).where(OAuth2Client.id == cid))
    client = result.scalar_one_or_none()
    if client is None:
        return RedirectResponse(url="/ui/admin/clients", status_code=302)

    from shomer.services.oauth2_client_service import OAuth2ClientService

    svc = OAuth2ClientService(db)
    _, new_secret = await svc.rotate_secret(client.client_id)

    ct = client.client_type
    am = client.token_endpoint_auth_method
    client_data = {
        "id": str(client.id),
        "client_id": client.client_id,
        "client_name": client.client_name,
        "client_type": ct.value if hasattr(ct, "value") else str(ct),
        "token_endpoint_auth_method": am.value if hasattr(am, "value") else str(am),
        "redirect_uris": client.redirect_uris,
        "grant_types": client.grant_types,
        "scopes": client.scopes,
        "is_active": client.is_active,
    }

    return _render(
        request,
        "admin/client_detail.html",
        {
            "client_data": client_data,
            "section": "clients",
            "success": "Secret rotated successfully",
            "new_secret": new_secret,
        },
    )


# ---------------------------------------------------------------------------
# Sessions UI
# ---------------------------------------------------------------------------


@router.get("/sessions", response_class=HTMLResponse)
async def admin_sessions_list(request: Request, db: DbSession) -> Any:
    """Render the admin sessions list page.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.

    Returns
    -------
    HTMLResponse
        Sessions list page or redirect.
    """
    admin = await _get_admin_user(request, db)
    if admin is None:
        return RedirectResponse(
            url="/ui/login?next=/ui/admin/sessions", status_code=302
        )

    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Session)
        .where(Session.expires_at > now)
        .order_by(Session.created_at.desc())
        .limit(100)
    )
    sessions_list = list(result.scalars().all())

    items = [
        {
            "id": str(s.id),
            "user_id": str(s.user_id),
            "ip_address": s.ip_address,
            "last_activity": s.last_activity.isoformat() if s.last_activity else None,
            "expires_at": s.expires_at.isoformat() if s.expires_at else None,
        }
        for s in sessions_list
    ]

    return _render(
        request,
        "admin/sessions_list.html",
        {"sessions": items, "section": "sessions"},
    )


@router.post("/sessions/{session_id}/revoke", response_class=HTMLResponse)
async def admin_session_revoke(request: Request, session_id: str, db: DbSession) -> Any:
    """Revoke a session from the UI.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    session_id : str
        UUID of the session to revoke.
    db : DbSession
        Database session.

    Returns
    -------
    HTMLResponse
        Redirect to sessions list.
    """
    admin = await _get_admin_user(request, db)
    if admin is None:
        return RedirectResponse(url="/ui/login", status_code=302)

    import uuid as _uuid

    try:
        sid = _uuid.UUID(session_id)
    except ValueError:
        return RedirectResponse(url="/ui/admin/sessions", status_code=302)

    result = await db.execute(select(Session).where(Session.id == sid))
    session_obj = result.scalar_one_or_none()
    if session_obj:
        await db.delete(session_obj)
        await db.flush()

    return RedirectResponse(url="/ui/admin/sessions", status_code=302)


# ---------------------------------------------------------------------------
# JWKS UI
# ---------------------------------------------------------------------------


@router.get("/jwks", response_class=HTMLResponse)
async def admin_jwks_list(request: Request, db: DbSession) -> Any:
    """Render the JWKS keys page.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.

    Returns
    -------
    HTMLResponse
        JWKS page or redirect.
    """
    admin = await _get_admin_user(request, db)
    if admin is None:
        return RedirectResponse(url="/ui/login?next=/ui/admin/jwks", status_code=302)

    from shomer.models.jwk import JWK

    result = await db.execute(select(JWK).order_by(JWK.created_at.desc()))
    keys_list = list(result.scalars().all())

    items = []
    for k in keys_list:
        st = k.status
        items.append(
            {
                "kid": k.kid,
                "algorithm": k.algorithm,
                "status": st.value if hasattr(st, "value") else str(st),
                "created_at": k.created_at.isoformat() if k.created_at else None,
            }
        )

    return _render(
        request,
        "admin/jwks_list.html",
        {"keys": items, "section": "jwks", "success": None},
    )


@router.post("/jwks/rotate", response_class=HTMLResponse)
async def admin_jwks_rotate(request: Request, db: DbSession) -> Any:
    """Trigger key rotation from the UI.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.

    Returns
    -------
    HTMLResponse
        Redirect to JWKS page.
    """
    admin = await _get_admin_user(request, db)
    if admin is None:
        return RedirectResponse(url="/ui/login", status_code=302)

    from shomer.core.security import AESEncryption
    from shomer.core.settings import get_settings
    from shomer.services.jwk_service import JWKService

    settings = get_settings()
    encryption = AESEncryption(settings.jwk_encryption_key.encode())
    svc = JWKService(db, encryption)
    await svc.rotate()

    return RedirectResponse(url="/ui/admin/jwks", status_code=302)


@router.post("/jwks/{kid}/revoke", response_class=HTMLResponse)
async def admin_jwks_revoke(request: Request, kid: str, db: DbSession) -> Any:
    """Revoke a key from the UI.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    kid : str
        Key ID to revoke.
    db : DbSession
        Database session.

    Returns
    -------
    HTMLResponse
        Redirect to JWKS page.
    """
    admin = await _get_admin_user(request, db)
    if admin is None:
        return RedirectResponse(url="/ui/login", status_code=302)

    from shomer.core.security import AESEncryption
    from shomer.core.settings import get_settings
    from shomer.services.jwk_service import JWKService

    settings = get_settings()
    encryption = AESEncryption(settings.jwk_encryption_key.encode())
    svc = JWKService(db, encryption)
    await svc.revoke(kid)

    return RedirectResponse(url="/ui/admin/jwks", status_code=302)


# ---------------------------------------------------------------------------
# Roles & Scopes UI
# ---------------------------------------------------------------------------


@router.get("/roles", response_class=HTMLResponse)
async def admin_roles_list(request: Request, db: DbSession) -> Any:
    """Render the roles and scopes management page.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.

    Returns
    -------
    HTMLResponse
        Roles/scopes page or redirect.
    """
    admin = await _get_admin_user(request, db)
    if admin is None:
        return RedirectResponse(url="/ui/login?next=/ui/admin/roles", status_code=302)

    from shomer.models.role import Role
    from shomer.models.scope import Scope

    roles_r = await db.execute(
        select(Role).options(selectinload(Role.scopes)).order_by(Role.name)
    )
    roles = [
        {
            "name": r.name,
            "description": r.description,
            "is_system": r.is_system,
            "scopes": [s.name for s in r.scopes],
        }
        for r in roles_r.scalars().all()
    ]

    scopes_r = await db.execute(select(Scope).order_by(Scope.name))
    scopes = [
        {"name": s.name, "description": s.description} for s in scopes_r.scalars().all()
    ]

    return _render(
        request,
        "admin/roles_list.html",
        {"roles": roles, "scopes": scopes, "section": "roles", "success": None},
    )


# ---------------------------------------------------------------------------
# PATs UI
# ---------------------------------------------------------------------------


@router.get("/pats", response_class=HTMLResponse)
async def admin_pats_list(request: Request, db: DbSession) -> Any:
    """Render the PATs oversight page.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.

    Returns
    -------
    HTMLResponse
        PATs list page or redirect.
    """
    admin = await _get_admin_user(request, db)
    if admin is None:
        return RedirectResponse(url="/ui/login?next=/ui/admin/pats", status_code=302)

    from shomer.models.personal_access_token import PersonalAccessToken

    result = await db.execute(
        select(PersonalAccessToken)
        .order_by(PersonalAccessToken.created_at.desc())
        .limit(100)
    )
    pats = [
        {
            "id": str(p.id),
            "name": p.name,
            "token_prefix": p.token_prefix,
            "user_id": str(p.user_id),
            "is_revoked": p.is_revoked,
        }
        for p in result.scalars().all()
    ]

    return _render(
        request,
        "admin/pats_list.html",
        {"pats": pats, "section": "pats"},
    )


@router.post("/pats/{pat_id}/revoke", response_class=HTMLResponse)
async def admin_pat_revoke(request: Request, pat_id: str, db: DbSession) -> Any:
    """Revoke a PAT from the UI.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    pat_id : str
        UUID of the PAT to revoke.
    db : DbSession
        Database session.

    Returns
    -------
    HTMLResponse
        Redirect to PATs list.
    """
    admin = await _get_admin_user(request, db)
    if admin is None:
        return RedirectResponse(url="/ui/login", status_code=302)

    import uuid as _uuid

    from shomer.models.personal_access_token import PersonalAccessToken

    try:
        pid = _uuid.UUID(pat_id)
    except ValueError:
        return RedirectResponse(url="/ui/admin/pats", status_code=302)

    result = await db.execute(
        select(PersonalAccessToken).where(PersonalAccessToken.id == pid)
    )
    pat = result.scalar_one_or_none()
    if pat:
        pat.is_revoked = True
        await db.flush()

    return RedirectResponse(url="/ui/admin/pats", status_code=302)


# ---------------------------------------------------------------------------
# Tenants UI
# ---------------------------------------------------------------------------


@router.get("/tenants", response_class=HTMLResponse)
async def admin_tenants_list(request: Request, db: DbSession) -> Any:
    """Render the tenants management page.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.

    Returns
    -------
    HTMLResponse
        Tenants list page or redirect.
    """
    admin = await _get_admin_user(request, db)
    if admin is None:
        return RedirectResponse(url="/ui/login?next=/ui/admin/tenants", status_code=302)

    from shomer.models.tenant import Tenant

    result = await db.execute(select(Tenant).order_by(Tenant.created_at.desc()))
    tenants = []
    for t in result.scalars().all():
        tm = t.trust_mode
        tenants.append(
            {
                "slug": t.slug,
                "display_name": t.display_name,
                "trust_mode": tm.value if hasattr(tm, "value") else str(tm),
                "is_active": t.is_active,
                "custom_domain": t.custom_domain,
            }
        )

    return _render(
        request,
        "admin/tenants_list.html",
        {"tenants": tenants, "section": "tenants"},
    )

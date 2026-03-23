# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Admin UI routes (Jinja2/HTMX).

Dashboard and management pages for administrators.
Requires session authentication and admin scope.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Request
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

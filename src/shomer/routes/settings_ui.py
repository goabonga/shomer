# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Browser-facing user settings UI routes (Jinja2/HTMX).

Profile, email management, and security settings pages.
Requires session authentication.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from shomer.deps import DbSession
from shomer.models.session import Session
from shomer.models.user import User
from shomer.services.session_service import SessionService

router = APIRouter(prefix="/ui/settings", tags=["ui"], include_in_schema=False)


def _templates() -> Jinja2Templates:
    """Get the Jinja2 templates instance."""
    from shomer.app import templates

    return templates


def _render(request: Request, template: str, ctx: dict[str, Any] | None = None) -> Any:
    """Render a template with the given context."""
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


@router.get("/profile", response_class=HTMLResponse)
async def settings_profile(request: Request, db: DbSession) -> Any:
    """Render the profile settings page.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.

    Returns
    -------
    HTMLResponse
        Profile settings page or redirect to login.
    """
    auth = await _get_session_user(request, db)
    if auth is None:
        return RedirectResponse(
            url="/ui/login?next=/ui/settings/profile", status_code=302
        )

    _, user = auth
    profile = user.profile

    return _render(
        request,
        "settings/profile.html",
        {
            "user": user,
            "profile": profile,
            "section": "profile",
        },
    )


@router.get("/emails", response_class=HTMLResponse)
async def settings_emails(request: Request, db: DbSession) -> Any:
    """Render the email management settings page.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.

    Returns
    -------
    HTMLResponse
        Email settings page or redirect to login.
    """
    auth = await _get_session_user(request, db)
    if auth is None:
        return RedirectResponse(
            url="/ui/login?next=/ui/settings/emails", status_code=302
        )

    _, user = auth

    return _render(
        request,
        "settings/emails.html",
        {
            "user": user,
            "emails": user.emails,
            "section": "emails",
        },
    )


@router.get("/security", response_class=HTMLResponse)
async def settings_security(request: Request, db: DbSession) -> Any:
    """Render the security settings page.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.

    Returns
    -------
    HTMLResponse
        Security settings page or redirect to login.
    """
    auth = await _get_session_user(request, db)
    if auth is None:
        return RedirectResponse(
            url="/ui/login?next=/ui/settings/security", status_code=302
        )

    session, user = auth

    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    count_stmt = (
        select(func.count())
        .select_from(Session)
        .where(Session.user_id == user.id, Session.expires_at > now)
    )
    count_result = await db.execute(count_stmt)
    active_sessions = count_result.scalar() or 0

    return _render(
        request,
        "settings/security.html",
        {
            "user": user,
            "active_sessions": active_sessions,
            "section": "security",
        },
    )

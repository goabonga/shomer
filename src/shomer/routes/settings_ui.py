# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Browser-facing user settings UI routes (Jinja2/HTMX).

Profile, email management, and security settings pages.
Requires session authentication.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from shomer.deps import DbSession
from shomer.models.session import Session
from shomer.models.user import User
from shomer.models.user_profile import UserProfile
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
    primary_email = next(
        (e.email for e in user.emails if e.is_primary),
        user.emails[0].email if user.emails else None,
    )

    return _render(
        request,
        "settings/profile.html",
        {
            "user": user,
            "profile": profile,
            "email": primary_email,
            "section": "profile",
            "success": None,
            "error": None,
        },
    )


# All profile form fields accepted by the POST handler.
_PROFILE_FIELDS = (
    "nickname",
    "preferred_username",
    "given_name",
    "middle_name",
    "family_name",
    "gender",
    "birthdate",
    "zoneinfo",
    "locale",
    "phone_number",
    "website",
    "profile_url",
    "picture_url",
    "address_street",
    "address_locality",
    "address_region",
    "address_postal_code",
    "address_country",
)


@router.post("/profile", response_class=HTMLResponse)
async def settings_profile_update(
    request: Request,
    db: DbSession,
    nickname: str | None = Form(None),
    preferred_username: str | None = Form(None),
    given_name: str | None = Form(None),
    middle_name: str | None = Form(None),
    family_name: str | None = Form(None),
    gender: str | None = Form(None),
    birthdate: str | None = Form(None),
    zoneinfo: str | None = Form(None),
    locale: str | None = Form(None),
    phone_number: str | None = Form(None),
    website: str | None = Form(None),
    profile_url: str | None = Form(None),
    picture_url: str | None = Form(None),
    address_street: str | None = Form(None),
    address_locality: str | None = Form(None),
    address_region: str | None = Form(None),
    address_postal_code: str | None = Form(None),
    address_country: str | None = Form(None),
) -> Any:
    """Handle profile form submission and update user profile.

    Creates the profile if it does not exist yet. Only provided
    (non-empty) fields are persisted.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.
    nickname : str or None
        Display name.
    preferred_username : str or None
        Preferred username.
    given_name : str or None
        First name.
    middle_name : str or None
        Middle name.
    family_name : str or None
        Last name.
    gender : str or None
        Gender.
    birthdate : str or None
        Birthday (YYYY-MM-DD).
    zoneinfo : str or None
        Timezone (e.g. Europe/Paris).
    locale : str or None
        Locale (e.g. en-US).
    phone_number : str or None
        Phone number.
    website : str or None
        Website URL.
    profile_url : str or None
        Profile page URL.
    picture_url : str or None
        Profile picture URL.
    address_street : str or None
        Street address.
    address_locality : str or None
        City.
    address_region : str or None
        State / province.
    address_postal_code : str or None
        Postal code.
    address_country : str or None
        Country.

    Returns
    -------
    HTMLResponse
        Profile page with success/error message, or redirect to login.
    """
    auth = await _get_session_user(request, db)
    if auth is None:
        return RedirectResponse(
            url="/ui/login?next=/ui/settings/profile", status_code=302
        )

    _, user = auth

    # Get or create profile
    profile = user.profile
    if profile is None:
        profile = UserProfile(user_id=user.id)
        db.add(profile)

    # Collect form values from locals
    form_values = {
        "nickname": nickname,
        "preferred_username": preferred_username,
        "given_name": given_name,
        "middle_name": middle_name,
        "family_name": family_name,
        "gender": gender,
        "birthdate": birthdate,
        "zoneinfo": zoneinfo,
        "locale": locale,
        "phone_number": phone_number,
        "website": website,
        "profile_url": profile_url,
        "picture_url": picture_url,
        "address_street": address_street,
        "address_locality": address_locality,
        "address_region": address_region,
        "address_postal_code": address_postal_code,
        "address_country": address_country,
    }

    for field in _PROFILE_FIELDS:
        value = form_values.get(field)
        setattr(profile, field, value if value else None)

    await db.flush()

    primary_email = next(
        (e.email for e in user.emails if e.is_primary),
        user.emails[0].email if user.emails else None,
    )

    return _render(
        request,
        "settings/profile.html",
        {
            "user": user,
            "profile": profile,
            "email": primary_email,
            "section": "profile",
            "success": "Profile updated successfully.",
            "error": None,
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

    # Query MFA status
    from shomer.models.user_mfa import UserMFA

    mfa_stmt = select(UserMFA).where(UserMFA.user_id == user.id)
    mfa_result = await db.execute(mfa_stmt)
    user_mfa = mfa_result.scalar_one_or_none()

    mfa_enabled = user_mfa.is_enabled if user_mfa else False
    mfa_methods = user_mfa.methods if user_mfa and user_mfa.is_enabled else []

    return _render(
        request,
        "settings/security.html",
        {
            "user": user,
            "active_sessions": active_sessions,
            "mfa_enabled": mfa_enabled,
            "mfa_methods": mfa_methods,
            "section": "security",
        },
    )

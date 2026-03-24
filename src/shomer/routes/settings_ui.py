# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Browser-facing user settings UI routes (Jinja2/HTMX).

Profile, email management, and security settings pages.
Requires session authentication.
"""

from __future__ import annotations

import uuid as uuid_mod
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from shomer.core.settings import get_settings
from shomer.deps import DbSession
from shomer.models.personal_access_token import PersonalAccessToken
from shomer.models.session import Session
from shomer.models.user import User
from shomer.models.user_profile import UserProfile
from shomer.services.session_service import SessionService

router = APIRouter(prefix="/ui/settings", tags=["ui"], include_in_schema=False)

_ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
_AVATAR_EXT: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}
_MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5 MB


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


#: Profile fields considered for completeness calculation.
_COMPLETENESS_FIELDS = (
    "nickname",
    "given_name",
    "family_name",
    "picture_url",
    "phone_number",
    "locale",
    "zoneinfo",
)


@router.get("", response_class=HTMLResponse)
async def settings_index(request: Request, db: DbSession) -> Any:
    """Render the settings index / dashboard page.

    Shows an at-a-glance overview of account status: profile completeness,
    email verification, MFA status, active sessions count, and PAT count.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.

    Returns
    -------
    HTMLResponse
        Settings index page or redirect to login.
    """
    auth = await _get_session_user(request, db)
    if auth is None:
        return RedirectResponse(url="/ui/login?next=/ui/settings", status_code=302)

    _, user = auth
    profile = user.profile

    # Profile completeness
    filled = 0
    total = len(_COMPLETENESS_FIELDS)
    if profile is not None:
        for field in _COMPLETENESS_FIELDS:
            if getattr(profile, field, None):
                filled += 1
    completeness = round(filled / total * 100) if total > 0 else 0

    # Email verification status
    has_verified_email = any(e.is_verified for e in user.emails)

    # MFA status
    from shomer.models.user_mfa import UserMFA

    mfa_stmt = select(UserMFA).where(UserMFA.user_id == user.id)
    mfa_result = await db.execute(mfa_stmt)
    user_mfa = mfa_result.scalar_one_or_none()
    mfa_enabled = user_mfa.is_enabled if user_mfa else False

    # Active sessions count
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    sessions_stmt = (
        select(func.count())
        .select_from(Session)
        .where(Session.user_id == user.id, Session.expires_at > now)
    )
    sessions_result = await db.execute(sessions_stmt)
    active_sessions = sessions_result.scalar() or 0

    # Active PAT count
    pat_stmt = (
        select(func.count())
        .select_from(PersonalAccessToken)
        .where(
            PersonalAccessToken.user_id == user.id,
            PersonalAccessToken.is_revoked == False,  # noqa: E712
        )
    )
    pat_result = await db.execute(pat_stmt)
    active_pats = pat_result.scalar() or 0

    return _render(
        request,
        "settings/index.html",
        {
            "user": user,
            "completeness": completeness,
            "has_verified_email": has_verified_email,
            "mfa_enabled": mfa_enabled,
            "active_sessions": active_sessions,
            "active_pats": active_pats,
            "section": "overview",
        },
    )


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


def _build_profile_ctx(
    user: Any,
    *,
    profile: Any | None = None,
    success: str | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    """Build template context for the profile settings page.

    Parameters
    ----------
    user : User
        The authenticated user.
    profile : UserProfile or None
        Explicit profile to use. Defaults to ``user.profile``.
    success : str or None
        Success flash message.
    error : str or None
        Error flash message.

    Returns
    -------
    dict
        Template context dictionary.
    """
    if profile is None:
        profile = user.profile
    primary_email = next(
        (e.email for e in user.emails if e.is_primary),
        user.emails[0].email if user.emails else None,
    )
    return {
        "user": user,
        "profile": profile,
        "email": primary_email,
        "section": "profile",
        "success": success,
        "error": error,
    }


@router.post("/profile/avatar", response_class=HTMLResponse)
async def settings_profile_avatar(
    request: Request,
    db: DbSession,
    avatar: UploadFile = File(...),
) -> Any:
    """Handle avatar file upload and update profile picture.

    Validates file type (JPEG, PNG, GIF, WebP) and size (max 5 MB),
    saves the file to the configured upload directory, and updates
    the user's ``picture_url``.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.
    avatar : UploadFile
        Uploaded avatar image file.

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

    # Validate content type
    content_type = avatar.content_type or ""
    if content_type not in _ALLOWED_AVATAR_TYPES:
        return _render(
            request,
            "settings/profile.html",
            _build_profile_ctx(
                user, error="Invalid file type. Use JPEG, PNG, GIF, or WebP."
            ),
        )

    # Read and validate size
    data = await avatar.read()
    if len(data) == 0:
        return _render(
            request,
            "settings/profile.html",
            _build_profile_ctx(user, error="File is empty."),
        )

    if len(data) > _MAX_AVATAR_SIZE:
        return _render(
            request,
            "settings/profile.html",
            _build_profile_ctx(user, error="File too large. Maximum size is 5 MB."),
        )

    # Determine file extension and generate unique filename
    ext = _AVATAR_EXT[content_type]
    filename = f"{uuid_mod.uuid4().hex}{ext}"

    # Save file to upload directory
    upload_dir = Path(get_settings().avatar_upload_dir) / str(user.id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Remove previous avatar files
    for old_file in upload_dir.iterdir():
        if old_file.is_file():
            old_file.unlink()

    (upload_dir / filename).write_bytes(data)

    # Update or create profile
    profile = user.profile
    if profile is None:
        profile = UserProfile(user_id=user.id)
        db.add(profile)

    profile.picture_url = f"/uploads/avatars/{user.id}/{filename}"
    await db.flush()

    return _render(
        request,
        "settings/profile.html",
        _build_profile_ctx(
            user, profile=profile, success="Avatar updated successfully."
        ),
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

    # Fetch active sessions list
    svc = SessionService(db)
    sessions = await svc.list_active(user.id)

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
            "sessions": sessions,
            "current_session_id": str(session.id),
            "active_sessions": len(sessions),
            "mfa_enabled": mfa_enabled,
            "mfa_methods": mfa_methods,
            "section": "security",
        },
    )

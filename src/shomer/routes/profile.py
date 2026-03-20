# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""First-party user profile and email management endpoints.

Returns the complete profile of the authenticated user including
emails, profile data, active sessions count, and tenant memberships.
Supports profile updates and multi-email management.
Distinct from ``/userinfo`` (OIDC standard).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from shomer.auth import CurrentUserInfo
from shomer.deps import CurrentUser, DbSession
from shomer.models.session import Session
from shomer.models.user import User
from shomer.models.user_email import UserEmail
from shomer.models.user_profile import UserProfile

router = APIRouter(prefix="/api", tags=["profile"])


@router.get("/me")
async def get_me(user: CurrentUser, db: DbSession) -> JSONResponse:
    """Return the authenticated user's full profile.

    Includes user info, emails, profile claims, active session count,
    and authentication method.

    Parameters
    ----------
    user : CurrentUser
        The authenticated user (Bearer or session).
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Complete user profile.
    """
    profile = await _build_profile(user, db)
    return JSONResponse(content=profile)


async def _build_profile(user: CurrentUserInfo, db: Any) -> dict[str, Any]:
    """Build the full user profile response.

    Parameters
    ----------
    user : CurrentUserInfo
        The authenticated user context.
    db : AsyncSession
        Database session.

    Returns
    -------
    dict[str, Any]
        User profile data.
    """
    result: dict[str, Any] = {
        "user_id": str(user.user_id),
        "auth_method": user.auth_method,
        "scopes": user.scopes,
    }

    # Look up user with profile and emails
    stmt = (
        select(User)
        .where(User.id == user.user_id)
        .options(selectinload(User.profile), selectinload(User.emails))
    )
    db_result = await db.execute(stmt)
    db_user = db_result.scalar_one_or_none()

    if db_user is None:
        return result

    result["username"] = db_user.username
    result["is_active"] = db_user.is_active

    # Emails
    result["emails"] = [
        {
            "email": e.email,
            "is_primary": e.is_primary,
            "is_verified": e.is_verified,
        }
        for e in db_user.emails
    ]

    # Profile
    if db_user.profile is not None:
        p = db_user.profile
        profile_data: dict[str, Any] = {}
        for field in (
            "name",
            "given_name",
            "family_name",
            "nickname",
            "preferred_username",
            "gender",
            "birthdate",
            "zoneinfo",
            "locale",
        ):
            val = getattr(p, field, None)
            if val is not None:
                profile_data[field] = val
        if p.picture_url:
            profile_data["picture"] = p.picture_url
        if p.profile_url:
            profile_data["profile"] = p.profile_url
        result["profile"] = profile_data
    else:
        result["profile"] = None

    # Active sessions count
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    session_count_stmt = (
        select(func.count())
        .select_from(Session)
        .where(
            Session.user_id == user.user_id,
            Session.expires_at > now,
        )
    )
    count_result = await db.execute(session_count_stmt)
    result["active_sessions"] = count_result.scalar() or 0

    # Tenant memberships (placeholder — M18)
    result["tenants"] = []

    return result


# --- Request models ---


class ProfileUpdateRequest(BaseModel):
    """Request body for PUT /api/me/profile.

    All fields are optional — only provided fields are updated.

    Attributes
    ----------
    name : str or None
        Full name.
    given_name : str or None
        First name.
    family_name : str or None
        Last name.
    nickname : str or None
        Casual name.
    preferred_username : str or None
        Preferred username.
    gender : str or None
        Gender.
    birthdate : str or None
        Birthday (YYYY-MM-DD).
    zoneinfo : str or None
        Timezone (e.g. Europe/Paris).
    locale : str or None
        Locale (e.g. fr-FR).
    picture : str or None
        Profile picture URL.
    website : str or None
        Website URL.
    """

    name: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    nickname: str | None = None
    preferred_username: str | None = None
    gender: str | None = None
    birthdate: str | None = None
    zoneinfo: str | None = None
    locale: str | None = None
    picture: str | None = None
    website: str | None = None


class AddEmailRequest(BaseModel):
    """Request body for POST /api/me/emails.

    Attributes
    ----------
    email : EmailStr
        The email address to add.
    """

    email: EmailStr


# --- Endpoints ---


@router.put("/me/profile")
async def update_profile(
    body: ProfileUpdateRequest, user: CurrentUser, db: DbSession
) -> JSONResponse:
    """Update the authenticated user's profile fields.

    Creates the profile if it doesn't exist yet. Only provided (non-None)
    fields are updated.

    Parameters
    ----------
    body : ProfileUpdateRequest
        Profile fields to update.
    user : CurrentUser
        The authenticated user.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Updated profile data.
    """
    # Get or create profile
    stmt = select(UserProfile).where(UserProfile.user_id == user.user_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if profile is None:
        profile = UserProfile(user_id=user.user_id)
        db.add(profile)

    # Update only provided fields
    field_map = {
        "name": "name",
        "given_name": "given_name",
        "family_name": "family_name",
        "nickname": "nickname",
        "preferred_username": "preferred_username",
        "gender": "gender",
        "birthdate": "birthdate",
        "zoneinfo": "zoneinfo",
        "locale": "locale",
        "picture": "picture_url",
        "website": "website",
    }

    update_data = body.model_dump(exclude_unset=True)
    for req_field, model_field in field_map.items():
        if req_field in update_data:
            setattr(profile, model_field, update_data[req_field])

    await db.flush()

    return JSONResponse(
        content={"message": "Profile updated", "user_id": str(user.user_id)}
    )


@router.post("/me/emails", status_code=status.HTTP_201_CREATED)
async def add_email(
    body: AddEmailRequest, user: CurrentUser, db: DbSession
) -> JSONResponse:
    """Add a new email address to the user's account.

    Triggers a verification email. The new email is not primary and
    not verified until confirmed.

    Parameters
    ----------
    body : AddEmailRequest
        The email to add.
    user : CurrentUser
        The authenticated user.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Confirmation message.

    Raises
    ------
    HTTPException
        409 if the email is already registered.
    """
    # Check if email already exists
    existing = await db.execute(select(UserEmail).where(UserEmail.email == body.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    new_email = UserEmail(
        user_id=user.user_id,
        email=body.email,
        is_primary=False,
        is_verified=False,
    )
    db.add(new_email)
    await db.flush()

    # Trigger verification email
    from shomer.services.auth_service import AuthService

    svc = AuthService(db)
    code = svc._generate_code()

    from datetime import datetime, timedelta, timezone

    from shomer.models.verification_code import VerificationCode

    vc = VerificationCode(
        email=body.email,
        code=code,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
    )
    db.add(vc)
    await db.flush()

    from shomer.tasks.email import send_email_task

    send_email_task.delay(
        to=body.email,
        subject="Verify your email",
        template="verification.html",
        context={"code": code},
    )

    return JSONResponse(
        status_code=201,
        content={"message": "Email added. Check your inbox for verification."},
    )


@router.delete("/me/emails/{email_id}")
async def delete_email(email_id: str, user: CurrentUser, db: DbSession) -> JSONResponse:
    """Remove a non-primary email from the user's account.

    Parameters
    ----------
    email_id : str
        UUID of the email record to delete.
    user : CurrentUser
        The authenticated user.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Confirmation message.

    Raises
    ------
    HTTPException
        404 if email not found, 400 if trying to delete primary email.
    """
    import uuid as _uuid

    try:
        eid = _uuid.UUID(email_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email ID",
        )

    stmt = select(UserEmail).where(
        UserEmail.id == eid,
        UserEmail.user_id == user.user_id,
    )
    result = await db.execute(stmt)
    email_record = result.scalar_one_or_none()

    if email_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found",
        )

    if email_record.is_primary:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete primary email",
        )

    await db.delete(email_record)
    await db.flush()

    return JSONResponse(content={"message": "Email removed"})


@router.put("/me/emails/{email_id}/primary")
async def set_primary_email(
    email_id: str, user: CurrentUser, db: DbSession
) -> JSONResponse:
    """Set an email as the primary email address.

    The email must be verified before it can be set as primary.

    Parameters
    ----------
    email_id : str
        UUID of the email record.
    user : CurrentUser
        The authenticated user.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Confirmation message.

    Raises
    ------
    HTTPException
        404 if not found, 400 if unverified.
    """
    import uuid as _uuid

    try:
        eid = _uuid.UUID(email_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email ID",
        )

    # Get the target email
    stmt = select(UserEmail).where(
        UserEmail.id == eid,
        UserEmail.user_id == user.user_id,
    )
    result = await db.execute(stmt)
    target = result.scalar_one_or_none()

    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found",
        )

    if not target.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot set unverified email as primary",
        )

    # Unset current primary
    all_emails_stmt = select(UserEmail).where(
        UserEmail.user_id == user.user_id,
    )
    all_result = await db.execute(all_emails_stmt)
    for email in all_result.scalars().all():
        email.is_primary = email.id == eid

    await db.flush()

    return JSONResponse(content={"message": "Primary email updated"})

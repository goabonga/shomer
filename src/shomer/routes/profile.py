# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""First-party user profile endpoint.

Returns the complete profile of the authenticated user including
emails, profile data, active sessions count, and tenant memberships.
Distinct from ``/userinfo`` (OIDC standard).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from shomer.auth import CurrentUserInfo
from shomer.deps import CurrentUser, DbSession
from shomer.models.session import Session
from shomer.models.user import User

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

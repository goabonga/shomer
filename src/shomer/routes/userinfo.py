# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""OIDC UserInfo endpoint per OpenID Connect Core 1.0 §5.3."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from shomer.auth import CurrentUserInfo
from shomer.deps import CurrentUser, DbSession
from shomer.models.user import User
from shomer.models.user_profile import UserProfile

router = APIRouter(tags=["oidc"])


async def _build_userinfo(user: CurrentUserInfo, db: Any) -> dict[str, Any]:
    """Build the UserInfo response claims based on token scopes.

    Parameters
    ----------
    user : CurrentUserInfo
        The authenticated user context.
    db : AsyncSession
        Database session.

    Returns
    -------
    dict[str, Any]
        Claims to return in the UserInfo response.
    """
    claims: dict[str, Any] = {"sub": str(user.user_id)}
    scopes = set(user.scopes)

    # Look up user with profile and emails
    stmt = (
        select(User)
        .where(User.id == user.user_id)
        .options(selectinload(User.profile), selectinload(User.emails))
    )
    result = await db.execute(stmt)
    db_user = result.scalar_one_or_none()

    if db_user is None:
        return claims

    # email scope
    if "email" in scopes:
        primary_email = next((e for e in db_user.emails if e.is_primary), None)
        if primary_email:
            claims["email"] = primary_email.email
            claims["email_verified"] = primary_email.is_verified

    # profile scope
    if "profile" in scopes and db_user.profile is not None:
        profile = db_user.profile
        _add_if_set(claims, "name", profile.name)
        _add_if_set(claims, "given_name", profile.given_name)
        _add_if_set(claims, "family_name", profile.family_name)
        _add_if_set(claims, "middle_name", profile.middle_name)
        _add_if_set(claims, "nickname", profile.nickname)
        _add_if_set(claims, "preferred_username", profile.preferred_username)
        _add_if_set(claims, "profile", profile.profile_url)
        _add_if_set(claims, "picture", profile.picture_url)
        _add_if_set(claims, "website", profile.website)
        _add_if_set(claims, "gender", profile.gender)
        _add_if_set(claims, "birthdate", profile.birthdate)
        _add_if_set(claims, "zoneinfo", profile.zoneinfo)
        _add_if_set(claims, "locale", profile.locale)

    # address scope
    if "address" in scopes and db_user.profile is not None:
        address = _build_address(db_user.profile)
        if address:
            claims["address"] = address

    # phone scope
    if "phone" in scopes and db_user.profile is not None:
        if db_user.profile.phone_number:
            claims["phone_number"] = db_user.profile.phone_number
            claims["phone_number_verified"] = db_user.profile.phone_number_verified

    return claims


def _add_if_set(claims: dict[str, Any], key: str, value: Any) -> None:
    """Add a claim only if the value is not None."""
    if value is not None:
        claims[key] = value


def _build_address(profile: UserProfile) -> dict[str, str] | None:
    """Build OIDC address claim from profile fields.

    Parameters
    ----------
    profile : UserProfile
        The user profile.

    Returns
    -------
    dict[str, str] or None
        Address object per OIDC Core §5.1.1, or None if empty.
    """
    address: dict[str, str] = {}
    if profile.address_formatted:
        address["formatted"] = profile.address_formatted
    if profile.address_street:
        address["street_address"] = profile.address_street
    if profile.address_locality:
        address["locality"] = profile.address_locality
    if profile.address_region:
        address["region"] = profile.address_region
    if profile.address_postal_code:
        address["postal_code"] = profile.address_postal_code
    if profile.address_country:
        address["country"] = profile.address_country
    return address or None


@router.get("/userinfo")
async def userinfo_get(user: CurrentUser, db: DbSession) -> JSONResponse:
    """OIDC UserInfo endpoint (GET).

    Returns claims about the authenticated user based on the scopes
    granted to the access token.

    Parameters
    ----------
    user : CurrentUser
        The authenticated user (injected via Bearer token or session).
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        JSON object with user claims.
    """
    claims = await _build_userinfo(user, db)
    return JSONResponse(content=claims)


@router.post("/userinfo")
async def userinfo_post(user: CurrentUser, db: DbSession) -> JSONResponse:
    """OIDC UserInfo endpoint (POST).

    Identical to GET — both methods are supported per OIDC Core §5.3.

    Parameters
    ----------
    user : CurrentUser
        The authenticated user.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        JSON object with user claims.
    """
    claims = await _build_userinfo(user, db)
    return JSONResponse(content=claims)

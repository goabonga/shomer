# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Admin user management API endpoints.

CRUD operations for user administration with RBAC protection.
Requires the ``admin:users:read`` scope.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from shomer.deps import DbSession
from shomer.middleware.rbac import require_scope
from shomer.models.session import Session
from shomer.models.user import User
from shomer.models.user_email import UserEmail
from shomer.models.user_role import UserRole

router = APIRouter(prefix="/admin/users", tags=["admin"])


@router.get(
    "",
    dependencies=[Depends(require_scope("admin:users:read"))],
)
async def list_users(
    db: DbSession,
    q: str | None = Query(None, description="Search by username or email"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> JSONResponse:
    """List users with optional search, filter, and pagination.

    Parameters
    ----------
    db : DbSession
        Database session.
    q : str or None
        Search term matching username or email (case-insensitive).
    is_active : bool or None
        Filter by active/inactive status.
    page : int
        Page number (1-based).
    page_size : int
        Number of items per page (max 100).

    Returns
    -------
    JSONResponse
        Paginated list of users with total count.
    """
    # Base query with emails eagerly loaded
    stmt = select(User).options(selectinload(User.emails))

    # Search filter
    if q:
        pattern = f"%{q}%"
        stmt = stmt.outerjoin(UserEmail, User.id == UserEmail.user_id).where(
            or_(
                User.username.ilike(pattern),
                UserEmail.email.ilike(pattern),
            )
        )

    # Active filter
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)

    # Count total (before pagination)
    count_stmt = select(func.count()).select_from(
        stmt.with_only_columns(User.id).distinct().subquery()
    )
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    # Pagination
    offset = (page - 1) * page_size
    stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(page_size)

    # Deduplicate (outerjoin can produce duplicates)
    stmt = stmt.distinct()

    result = await db.execute(stmt)
    users = list(result.scalars().unique().all())

    items: list[dict[str, Any]] = []
    for user in users:
        primary_email = next(
            (e.email for e in user.emails if e.is_primary),
            user.emails[0].email if user.emails else None,
        )
        items.append(
            {
                "id": str(user.id),
                "username": user.username,
                "email": primary_email,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }
        )

    return JSONResponse(
        content={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.get(
    "/{user_id}",
    dependencies=[Depends(require_scope("admin:users:read"))],
)
async def get_user(user_id: str, db: DbSession) -> JSONResponse:
    """Get detailed user view including roles, emails, sessions, and memberships.

    Parameters
    ----------
    user_id : str
        UUID of the user to retrieve.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Detailed user data.

    Raises
    ------
    HTTPException
        400 if the user_id is not a valid UUID.
        404 if the user is not found.
    """
    import uuid as _uuid
    from datetime import datetime, timezone

    try:
        uid = _uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID",
        )

    stmt = (
        select(User)
        .where(User.id == uid)
        .options(
            selectinload(User.emails),
            selectinload(User.profile),
        )
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Emails
    emails = [
        {
            "id": str(e.id),
            "email": e.email,
            "is_primary": e.is_primary,
            "is_verified": e.is_verified,
        }
        for e in user.emails
    ]

    # Profile
    profile_data: dict[str, Any] | None = None
    if user.profile:
        p = user.profile
        profile_data = {}
        for field in (
            "name",
            "given_name",
            "family_name",
            "nickname",
            "preferred_username",
            "gender",
            "locale",
            "zoneinfo",
        ):
            val = getattr(p, field, None)
            if val is not None:
                profile_data[field] = val

    # Roles (via user_roles table)
    roles_stmt = (
        select(UserRole)
        .where(UserRole.user_id == uid)
        .options(selectinload(UserRole.role))
    )
    roles_result = await db.execute(roles_stmt)
    user_roles = list(roles_result.scalars().all())
    roles = [
        {
            "id": str(ur.role.id),
            "name": ur.role.name,
            "tenant_id": str(ur.tenant_id) if ur.tenant_id else None,
            "expires_at": ur.expires_at.isoformat() if ur.expires_at else None,
        }
        for ur in user_roles
    ]

    # Active sessions count
    now = datetime.now(timezone.utc)
    session_stmt = (
        select(func.count())
        .select_from(Session)
        .where(Session.user_id == uid, Session.expires_at > now)
    )
    session_result = await db.execute(session_stmt)
    active_sessions = session_result.scalar() or 0

    # Tenant memberships
    from shomer.models.tenant_member import TenantMember

    membership_stmt = select(TenantMember).where(TenantMember.user_id == uid)
    membership_result = await db.execute(membership_stmt)
    memberships = [
        {
            "tenant_id": str(m.tenant_id),
            "role": m.role,
            "joined_at": m.joined_at.isoformat() if m.joined_at else None,
        }
        for m in membership_result.scalars().all()
    ]

    return JSONResponse(
        content={
            "id": str(user.id),
            "username": user.username,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "emails": emails,
            "profile": profile_data,
            "roles": roles,
            "active_sessions": active_sessions,
            "memberships": memberships,
        }
    )


class AdminCreateUserRequest(BaseModel):
    """Request body for admin user creation.

    Attributes
    ----------
    email : EmailStr
        Email address for the new user.
    password : str
        Plain-text password (will be hashed with Argon2id).
    username : str or None
        Optional display name.
    is_active : bool
        Whether the account is active (default True).
    email_verified : bool
        Whether to mark the email as verified (admin bypass, default True).
    """

    email: EmailStr
    password: str
    username: str | None = None
    is_active: bool = True
    email_verified: bool = True


@router.post(
    "",
    dependencies=[Depends(require_scope("admin:users:write"))],
    status_code=status.HTTP_201_CREATED,
)
async def create_user(body: AdminCreateUserRequest, db: DbSession) -> JSONResponse:
    """Create a new user with admin bypass for email verification.

    Parameters
    ----------
    body : AdminCreateUserRequest
        User creation data.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        The created user ID and email.

    Raises
    ------
    HTTPException
        409 if the email is already registered.
    """
    # Check for existing email
    existing = await db.execute(select(UserEmail).where(UserEmail.email == body.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    from shomer.core.security import hash_password
    from shomer.models.queries import create_user as _create_user

    password_hash = hash_password(body.password)
    user = await _create_user(
        db,
        email=body.email,
        password_hash=password_hash,
        username=body.username,
    )

    # Admin bypass: set is_active and email_verified
    user.is_active = body.is_active

    if body.email_verified:
        email_record = next(
            (e for e in await _get_user_emails(db, user.id)),
            None,
        )
        if email_record:
            email_record.is_verified = True

    await db.flush()

    return JSONResponse(
        status_code=201,
        content={
            "id": str(user.id),
            "email": body.email,
            "username": body.username,
            "is_active": user.is_active,
            "email_verified": body.email_verified,
            "message": "User created successfully",
        },
    )


async def _get_user_emails(db: Any, user_id: Any) -> list[Any]:
    """Fetch all email records for a user.

    Parameters
    ----------
    db : AsyncSession
        Database session.
    user_id : uuid.UUID
        The user ID.

    Returns
    -------
    list
        List of UserEmail records.
    """
    result = await db.execute(select(UserEmail).where(UserEmail.user_id == user_id))
    return list(result.scalars().all())

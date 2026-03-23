# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Admin user management API endpoints.

CRUD operations for user administration with RBAC protection.
Requires the ``admin:users:read`` scope.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from shomer.deps import DbSession
from shomer.middleware.rbac import require_scope
from shomer.models.user import User
from shomer.models.user_email import UserEmail

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

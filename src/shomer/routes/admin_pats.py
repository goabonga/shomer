# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Admin PAT oversight API endpoints.

List, inspect, and revoke personal access tokens across all users.
Requires ``admin:pats:read`` or ``admin:pats:write`` scope.
"""

from __future__ import annotations

import uuid as _uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import func, select

from shomer.deps import DbSession
from shomer.middleware.rbac import require_scope
from shomer.models.personal_access_token import PersonalAccessToken

router = APIRouter(prefix="/admin/pats", tags=["admin"])


def _pat_to_dict(pat: Any) -> dict[str, Any]:
    """Serialize a PAT to a JSON-safe dict."""
    return {
        "id": str(pat.id),
        "user_id": str(pat.user_id),
        "name": pat.name,
        "token_prefix": pat.token_prefix,
        "scopes": pat.scopes,
        "is_revoked": pat.is_revoked,
        "expires_at": pat.expires_at.isoformat() if pat.expires_at else None,
        "last_used_at": pat.last_used_at.isoformat() if pat.last_used_at else None,
        "created_at": pat.created_at.isoformat() if pat.created_at else None,
    }


@router.get(
    "",
    dependencies=[Depends(require_scope("admin:pats:read"))],
)
async def list_pats(
    db: DbSession,
    user_id: str | None = Query(None, description="Filter by user UUID"),
    scope: str | None = Query(None, description="Filter by scope substring"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> JSONResponse:
    """List all PATs with optional filters and pagination.

    Parameters
    ----------
    db : DbSession
        Database session.
    user_id : str or None
        Filter by user UUID.
    scope : str or None
        Filter by scope substring (e.g. ``admin``).
    page : int
        Page number (1-based).
    page_size : int
        Items per page (max 100).

    Returns
    -------
    JSONResponse
        Paginated list of PATs.
    """
    stmt = select(PersonalAccessToken)

    if user_id:
        try:
            uid = _uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user_id",
            )
        stmt = stmt.where(PersonalAccessToken.user_id == uid)

    if scope:
        stmt = stmt.where(PersonalAccessToken.scopes.ilike(f"%{scope}%"))

    # Count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    stmt = (
        stmt.order_by(PersonalAccessToken.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    pats = list(result.scalars().all())

    return JSONResponse(
        content={
            "items": [_pat_to_dict(p) for p in pats],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.get(
    "/{pat_id}",
    dependencies=[Depends(require_scope("admin:pats:read"))],
)
async def get_pat(pat_id: str, db: DbSession) -> JSONResponse:
    """Get PAT details by ID.

    Parameters
    ----------
    pat_id : str
        UUID of the PAT.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        PAT details.

    Raises
    ------
    HTTPException
        400 if the pat_id is not a valid UUID.
        404 if the PAT is not found.
    """
    try:
        pid = _uuid.UUID(pat_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PAT ID",
        )

    result = await db.execute(
        select(PersonalAccessToken).where(PersonalAccessToken.id == pid)
    )
    pat = result.scalar_one_or_none()

    if pat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PAT not found",
        )

    return JSONResponse(content=_pat_to_dict(pat))


@router.delete(
    "/{pat_id}",
    dependencies=[Depends(require_scope("admin:pats:write"))],
)
async def revoke_pat(pat_id: str, db: DbSession) -> JSONResponse:
    """Revoke a PAT by ID.

    Sets ``is_revoked`` to True (soft revoke).

    Parameters
    ----------
    pat_id : str
        UUID of the PAT to revoke.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Confirmation message.

    Raises
    ------
    HTTPException
        400 if the pat_id is not a valid UUID.
        404 if the PAT is not found.
    """
    try:
        pid = _uuid.UUID(pat_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PAT ID",
        )

    result = await db.execute(
        select(PersonalAccessToken).where(PersonalAccessToken.id == pid)
    )
    pat = result.scalar_one_or_none()

    if pat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PAT not found",
        )

    pat.is_revoked = True
    await db.flush()

    return JSONResponse(content={"id": str(pid), "message": "PAT revoked successfully"})

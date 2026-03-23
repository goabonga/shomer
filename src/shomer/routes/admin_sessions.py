# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Admin session management API endpoints.

List, inspect, and revoke user sessions with RBAC protection.
Requires ``admin:sessions:read`` or ``admin:sessions:write`` scope.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select

from shomer.deps import DbSession
from shomer.middleware.rbac import require_scope
from shomer.models.session import Session

router = APIRouter(prefix="/admin/sessions", tags=["admin"])


@router.get(
    "",
    dependencies=[Depends(require_scope("admin:sessions:read"))],
)
async def list_sessions(
    db: DbSession,
    user_id: str | None = Query(None, description="Filter by user UUID"),
    tenant_id: str | None = Query(None, description="Filter by tenant UUID"),
    active_only: bool = Query(True, description="Only show non-expired sessions"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> JSONResponse:
    """List sessions with optional filters and pagination.

    Parameters
    ----------
    db : DbSession
        Database session.
    user_id : str or None
        Filter by user UUID.
    tenant_id : str or None
        Filter by tenant UUID.
    active_only : bool
        If True (default), only return non-expired sessions.
    page : int
        Page number (1-based).
    page_size : int
        Number of items per page (max 100).

    Returns
    -------
    JSONResponse
        Paginated list of sessions with total count.
    """
    import uuid as _uuid
    from datetime import datetime, timezone

    stmt = select(Session)

    if user_id:
        try:
            uid = _uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user_id",
            )
        stmt = stmt.where(Session.user_id == uid)

    if tenant_id:
        try:
            tid = _uuid.UUID(tenant_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tenant_id",
            )
        stmt = stmt.where(Session.tenant_id == tid)

    if active_only:
        now = datetime.now(timezone.utc)
        stmt = stmt.where(Session.expires_at > now)

    # Count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    stmt = stmt.order_by(Session.created_at.desc()).offset(offset).limit(page_size)

    result = await db.execute(stmt)
    sessions = list(result.scalars().all())

    items: list[dict[str, Any]] = []
    for s in sessions:
        items.append(
            {
                "id": str(s.id),
                "user_id": str(s.user_id),
                "tenant_id": str(s.tenant_id) if s.tenant_id else None,
                "ip_address": s.ip_address,
                "user_agent": s.user_agent,
                "last_activity": s.last_activity.isoformat()
                if s.last_activity
                else None,
                "expires_at": s.expires_at.isoformat() if s.expires_at else None,
                "created_at": s.created_at.isoformat() if s.created_at else None,
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
    "/{session_id}",
    dependencies=[Depends(require_scope("admin:sessions:read"))],
)
async def get_session(session_id: str, db: DbSession) -> JSONResponse:
    """Get session details by ID.

    Parameters
    ----------
    session_id : str
        UUID of the session.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Session details.

    Raises
    ------
    HTTPException
        400 if the session_id is not a valid UUID.
        404 if the session is not found.
    """
    import uuid as _uuid

    try:
        sid = _uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID",
        )

    result = await db.execute(select(Session).where(Session.id == sid))
    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    return JSONResponse(
        content={
            "id": str(session.id),
            "user_id": str(session.user_id),
            "tenant_id": str(session.tenant_id) if session.tenant_id else None,
            "ip_address": session.ip_address,
            "user_agent": session.user_agent,
            "last_activity": session.last_activity.isoformat()
            if session.last_activity
            else None,
            "expires_at": session.expires_at.isoformat()
            if session.expires_at
            else None,
            "created_at": session.created_at.isoformat()
            if session.created_at
            else None,
        }
    )


@router.delete(
    "/{session_id}",
    dependencies=[Depends(require_scope("admin:sessions:write"))],
)
async def revoke_session(session_id: str, db: DbSession) -> JSONResponse:
    """Revoke (delete) a single session.

    Parameters
    ----------
    session_id : str
        UUID of the session to revoke.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Confirmation message.

    Raises
    ------
    HTTPException
        400 if the session_id is not a valid UUID.
        404 if the session is not found.
    """
    import uuid as _uuid

    try:
        sid = _uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID",
        )

    result = await db.execute(select(Session).where(Session.id == sid))
    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    await db.delete(session)
    await db.flush()

    return JSONResponse(
        content={"id": str(sid), "message": "Session revoked successfully"}
    )


@router.delete(
    "/users/{user_id}",
    dependencies=[Depends(require_scope("admin:sessions:write"))],
)
async def revoke_user_sessions(user_id: str, db: DbSession) -> JSONResponse:
    """Revoke all sessions for a specific user.

    Parameters
    ----------
    user_id : str
        UUID of the user whose sessions should be revoked.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Count of revoked sessions.

    Raises
    ------
    HTTPException
        400 if the user_id is not a valid UUID.
    """
    import uuid as _uuid

    try:
        uid = _uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID",
        )

    result = await db.execute(
        sa_delete(Session).where(Session.user_id == uid).returning(Session.id)
    )
    deleted_ids = list(result.scalars().all())
    await db.flush()

    return JSONResponse(
        content={
            "user_id": str(uid),
            "revoked_count": len(deleted_ids),
            "message": "All user sessions revoked",
        }
    )

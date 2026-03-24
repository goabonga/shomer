# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Personal Access Token management API endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from shomer.deps import CurrentUser, DbSession
from shomer.services.pat_service import PATError, PATService

router = APIRouter(prefix="/api/pats", tags=["pat"])


class PATCreateRequest(BaseModel):
    """Request body for PAT creation.

    Attributes
    ----------
    name : str
        Human-readable label for the token.
    scopes : str
        Space-separated scopes.
    expires_at : datetime or None
        Optional expiration timestamp.
    """

    name: str
    scopes: str = ""
    expires_at: datetime | None = None


@router.post("")
async def create_pat(
    body: PATCreateRequest, user: CurrentUser, db: DbSession
) -> JSONResponse:
    """Create a new Personal Access Token.

    Returns the raw token value **once**. It cannot be retrieved later.

    Parameters
    ----------
    body : PATCreateRequest
        Token name, scopes, and optional expiration.
    user : CurrentUser
        The authenticated user.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        The created PAT including the raw token.
    """
    svc = PATService(db)
    result = await svc.create(
        user_id=user.user_id,
        name=body.name,
        scopes=body.scopes,
        expires_at=body.expires_at,
    )

    return JSONResponse(
        status_code=201,
        content={
            "id": str(result.id),
            "name": result.name,
            "token": result.token,
            "token_prefix": result.token_prefix,
            "scopes": result.scopes,
            "expires_at": result.expires_at.isoformat() if result.expires_at else None,
            "created_at": result.created_at.isoformat(),
            "message": "Save this token — it will not be shown again.",
        },
    )


@router.get("")
async def list_pats(user: CurrentUser, db: DbSession) -> JSONResponse:
    """List all PATs for the authenticated user.

    Returns metadata only — no raw token values.

    Parameters
    ----------
    user : CurrentUser
        The authenticated user.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        List of PAT metadata.
    """
    svc = PATService(db)
    pats = await svc.list_for_user(user.user_id)

    return JSONResponse(
        content={
            "tokens": [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "token_prefix": p.token_prefix,
                    "scopes": p.scopes,
                    "expires_at": p.expires_at.isoformat() if p.expires_at else None,
                    "last_used_at": (
                        p.last_used_at.isoformat() if p.last_used_at else None
                    ),
                    "last_used_ip": p.last_used_ip,
                    "use_count": p.use_count,
                    "is_revoked": p.is_revoked,
                    "created_at": p.created_at.isoformat(),
                }
                for p in pats
            ],
        },
    )


@router.delete("/{pat_id}")
async def revoke_pat(
    pat_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> JSONResponse:
    """Revoke a Personal Access Token.

    Parameters
    ----------
    pat_id : uuid.UUID
        The PAT record ID.
    user : CurrentUser
        The authenticated user.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Confirmation of revocation.
    """
    svc = PATService(db)
    try:
        await svc.revoke(pat_id, user.user_id)
    except PATError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        )

    return JSONResponse(content={"message": "Token revoked successfully."})

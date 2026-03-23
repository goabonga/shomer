# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Admin OAuth2 client management API endpoints.

CRUD operations for OAuth2 client administration with RBAC protection.
Requires the ``admin:clients:read`` or ``admin:clients:write`` scope.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import func, select

from shomer.deps import DbSession
from shomer.middleware.rbac import require_scope
from shomer.models.oauth2_client import OAuth2Client

router = APIRouter(prefix="/admin/clients", tags=["admin"])


def _client_type_str(c: Any) -> str:
    """Return the client_type as a plain string."""
    return (
        c.client_type.value if hasattr(c.client_type, "value") else str(c.client_type)
    )


def _auth_method_str(c: Any) -> str:
    """Return the token_endpoint_auth_method as a plain string."""
    m = c.token_endpoint_auth_method
    return m.value if hasattr(m, "value") else str(m)


@router.get(
    "",
    dependencies=[Depends(require_scope("admin:clients:read"))],
)
async def list_clients(
    db: DbSession,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> JSONResponse:
    """List OAuth2 clients with pagination.

    Parameters
    ----------
    db : DbSession
        Database session.
    page : int
        Page number (1-based).
    page_size : int
        Number of items per page (max 100).

    Returns
    -------
    JSONResponse
        Paginated list of OAuth2 clients with total count.
    """
    count_stmt = select(func.count()).select_from(OAuth2Client)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    offset = (page - 1) * page_size
    stmt = (
        select(OAuth2Client)
        .order_by(OAuth2Client.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    clients = list(result.scalars().all())

    items: list[dict[str, Any]] = []
    for c in clients:
        items.append(
            {
                "id": str(c.id),
                "client_id": c.client_id,
                "client_name": c.client_name,
                "client_type": _client_type_str(c),
                "is_active": c.is_active,
                "created_at": c.created_at.isoformat() if c.created_at else None,
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
    "/{client_db_id}",
    dependencies=[Depends(require_scope("admin:clients:read"))],
)
async def get_client(client_db_id: str, db: DbSession) -> JSONResponse:
    """Get OAuth2 client details by database ID.

    Parameters
    ----------
    client_db_id : str
        UUID of the client record.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Client details.

    Raises
    ------
    HTTPException
        400 if the ID is not a valid UUID.
        404 if the client is not found.
    """
    import uuid as _uuid

    try:
        cid = _uuid.UUID(client_db_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client ID",
        )

    result = await db.execute(select(OAuth2Client).where(OAuth2Client.id == cid))
    client = result.scalar_one_or_none()

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    return JSONResponse(
        content={
            "id": str(client.id),
            "client_id": client.client_id,
            "client_name": client.client_name,
            "client_type": _client_type_str(client),
            "redirect_uris": client.redirect_uris,
            "grant_types": client.grant_types,
            "response_types": client.response_types,
            "scopes": client.scopes,
            "token_endpoint_auth_method": _auth_method_str(client),
            "logo_uri": client.logo_uri,
            "tos_uri": client.tos_uri,
            "policy_uri": client.policy_uri,
            "contacts": client.contacts,
            "is_active": client.is_active,
            "created_at": client.created_at.isoformat() if client.created_at else None,
        }
    )


class AdminCreateClientRequest(BaseModel):
    """Request body for admin client creation.

    Attributes
    ----------
    client_name : str
        Human-readable name.
    client_type : str
        ``confidential`` or ``public``.
    redirect_uris : list[str]
        Allowed redirect URIs.
    grant_types : list[str]
        Allowed grant types.
    scopes : list[str]
        Allowed scopes.
    """

    client_name: str
    client_type: str = "confidential"
    redirect_uris: list[str] = []
    grant_types: list[str] = []
    scopes: list[str] = []


@router.post(
    "",
    dependencies=[Depends(require_scope("admin:clients:write"))],
    status_code=status.HTTP_201_CREATED,
)
async def create_client(body: AdminCreateClientRequest, db: DbSession) -> JSONResponse:
    """Create a new OAuth2 client with auto-generated credentials.

    Parameters
    ----------
    body : AdminCreateClientRequest
        Client creation data.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        The created client including the raw secret (shown once).
    """
    from shomer.models.oauth2_client import ClientType
    from shomer.services.oauth2_client_service import OAuth2ClientService

    try:
        client_type = ClientType(body.client_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid client_type: {body.client_type}",
        )

    svc = OAuth2ClientService(db)
    client, raw_secret = await svc.create_client(
        client_name=body.client_name,
        client_type=client_type,
        redirect_uris=body.redirect_uris,
        grant_types=body.grant_types,
        scopes=body.scopes,
    )

    return JSONResponse(
        status_code=201,
        content={
            "id": str(client.id),
            "client_id": client.client_id,
            "client_secret": raw_secret,
            "client_name": client.client_name,
            "client_type": _client_type_str(client),
            "message": "Client created successfully",
        },
    )


class AdminUpdateClientRequest(BaseModel):
    """Request body for admin client update.

    Attributes
    ----------
    client_name : str or None
        Human-readable name.
    redirect_uris : list[str] or None
        Allowed redirect URIs.
    grant_types : list[str] or None
        Allowed grant types.
    scopes : list[str] or None
        Allowed scopes.
    is_active : bool or None
        Active status.
    """

    client_name: str | None = None
    redirect_uris: list[str] | None = None
    grant_types: list[str] | None = None
    scopes: list[str] | None = None
    is_active: bool | None = None


@router.put(
    "/{client_db_id}",
    dependencies=[Depends(require_scope("admin:clients:write"))],
)
async def update_client(
    client_db_id: str, body: AdminUpdateClientRequest, db: DbSession
) -> JSONResponse:
    """Update an OAuth2 client's settings.

    Parameters
    ----------
    client_db_id : str
        UUID of the client record.
    body : AdminUpdateClientRequest
        Fields to update.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Updated client data.

    Raises
    ------
    HTTPException
        400 if the ID is not a valid UUID.
        404 if the client is not found.
    """
    import uuid as _uuid

    try:
        cid = _uuid.UUID(client_db_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client ID",
        )

    result = await db.execute(select(OAuth2Client).where(OAuth2Client.id == cid))
    client = result.scalar_one_or_none()

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    if body.client_name is not None:
        client.client_name = body.client_name
    if body.redirect_uris is not None:
        client.redirect_uris = body.redirect_uris
    if body.grant_types is not None:
        client.grant_types = body.grant_types
    if body.scopes is not None:
        client.scopes = body.scopes
    if body.is_active is not None:
        client.is_active = body.is_active

    await db.flush()

    return JSONResponse(
        content={
            "id": str(client.id),
            "client_id": client.client_id,
            "client_name": client.client_name,
            "is_active": client.is_active,
            "message": "Client updated successfully",
        }
    )


@router.delete(
    "/{client_db_id}",
    dependencies=[Depends(require_scope("admin:clients:write"))],
)
async def delete_client(client_db_id: str, db: DbSession) -> JSONResponse:
    """Delete an OAuth2 client (hard delete).

    Parameters
    ----------
    client_db_id : str
        UUID of the client record.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Confirmation message.

    Raises
    ------
    HTTPException
        400 if the ID is not a valid UUID.
        404 if the client is not found.
    """
    import uuid as _uuid

    try:
        cid = _uuid.UUID(client_db_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client ID",
        )

    result = await db.execute(select(OAuth2Client).where(OAuth2Client.id == cid))
    client = result.scalar_one_or_none()

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    await db.delete(client)
    await db.flush()

    return JSONResponse(
        content={"id": str(cid), "message": "Client deleted successfully"}
    )


@router.post(
    "/{client_db_id}/rotate-secret",
    dependencies=[Depends(require_scope("admin:clients:write"))],
)
async def rotate_client_secret(client_db_id: str, db: DbSession) -> JSONResponse:
    """Rotate the client secret for a confidential client.

    Parameters
    ----------
    client_db_id : str
        UUID of the client record.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        The new raw secret (shown once).

    Raises
    ------
    HTTPException
        400 if the ID is not valid or the client is public.
        404 if the client is not found.
    """
    import uuid as _uuid

    try:
        cid = _uuid.UUID(client_db_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client ID",
        )

    result = await db.execute(select(OAuth2Client).where(OAuth2Client.id == cid))
    client = result.scalar_one_or_none()

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    from shomer.models.oauth2_client import ClientType
    from shomer.services.oauth2_client_service import OAuth2ClientService

    ct = client.client_type
    ct_val = ct.value if hasattr(ct, "value") else str(ct)
    if ct_val != ClientType.CONFIDENTIAL.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot rotate secret for public client",
        )

    svc = OAuth2ClientService(db)
    _, new_secret = await svc.rotate_secret(client.client_id)

    return JSONResponse(
        content={
            "client_id": client.client_id,
            "client_secret": new_secret,
            "message": "Client secret rotated successfully",
        }
    )

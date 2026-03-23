# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Admin JWKS management API endpoints.

List, inspect, rotate, and revoke signing keys with RBAC protection.
Requires ``admin:jwks:read`` or ``admin:jwks:write`` scope.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import select

from shomer.deps import DbSession
from shomer.middleware.rbac import require_scope
from shomer.models.jwk import JWK

router = APIRouter(prefix="/admin/jwks", tags=["admin"])


def _jwk_status_str(jwk: Any) -> str:
    """Return the JWK status as a plain string."""
    s = jwk.status
    return s.value if hasattr(s, "value") else str(s)


def _jwk_to_dict(jwk: Any) -> dict[str, Any]:
    """Serialize a JWK record to a JSON-safe dict (public key only)."""
    public_key_data = json.loads(jwk.public_key) if jwk.public_key else None
    return {
        "id": str(jwk.id),
        "kid": jwk.kid,
        "algorithm": jwk.algorithm,
        "status": _jwk_status_str(jwk),
        "public_key": public_key_data,
        "created_at": jwk.created_at.isoformat() if jwk.created_at else None,
    }


@router.get(
    "",
    dependencies=[Depends(require_scope("admin:jwks:read"))],
)
async def list_keys(db: DbSession) -> JSONResponse:
    """List all JWK signing keys with their status.

    Parameters
    ----------
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        List of all keys (active, rotated, revoked).
    """
    result = await db.execute(select(JWK).order_by(JWK.created_at.desc()))
    keys = list(result.scalars().all())

    return JSONResponse(
        content={
            "keys": [_jwk_to_dict(k) for k in keys],
            "total": len(keys),
        }
    )


@router.get(
    "/{kid}",
    dependencies=[Depends(require_scope("admin:jwks:read"))],
)
async def get_key(kid: str, db: DbSession) -> JSONResponse:
    """Get key details by kid (public key only).

    Parameters
    ----------
    kid : str
        The key ID.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Key details with public key data.

    Raises
    ------
    HTTPException
        404 if the key is not found.
    """
    result = await db.execute(select(JWK).where(JWK.kid == kid))
    jwk = result.scalar_one_or_none()

    if jwk is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Key not found",
        )

    return JSONResponse(content=_jwk_to_dict(jwk))


@router.post(
    "/rotate",
    dependencies=[Depends(require_scope("admin:jwks:write"))],
)
async def rotate_key(db: DbSession) -> JSONResponse:
    """Trigger key rotation: generate a new active key.

    The current active key is moved to ``rotated`` status and remains
    available for signature verification.

    Parameters
    ----------
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        The newly created active key.
    """
    from shomer.core.security import AESEncryption
    from shomer.core.settings import get_settings
    from shomer.services.jwk_service import JWKService

    settings = get_settings()
    encryption = AESEncryption(settings.jwk_encryption_key.encode())
    svc = JWKService(db, encryption)
    new_key = await svc.rotate()

    return JSONResponse(
        content={
            **_jwk_to_dict(new_key),
            "message": "Key rotated successfully",
        }
    )


@router.delete(
    "/{kid}",
    dependencies=[Depends(require_scope("admin:jwks:write"))],
)
async def revoke_key(kid: str, db: DbSession) -> JSONResponse:
    """Revoke a key by its kid.

    Sets the key status to ``revoked``. Revoked keys are excluded
    from the public JWKS endpoint.

    Parameters
    ----------
    kid : str
        The key ID to revoke.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Confirmation message.

    Raises
    ------
    HTTPException
        404 if the key is not found.
    """
    from shomer.core.security import AESEncryption
    from shomer.core.settings import get_settings
    from shomer.services.jwk_service import JWKService

    settings = get_settings()
    encryption = AESEncryption(settings.jwk_encryption_key.encode())
    svc = JWKService(db, encryption)
    revoked = await svc.revoke(kid)

    if revoked is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Key not found",
        )

    return JSONResponse(
        content={"kid": kid, "status": "revoked", "message": "Key revoked successfully"}
    )

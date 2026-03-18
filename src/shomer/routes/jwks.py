# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""JWKS endpoint — RFC 7517 JWK Set."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import select

from shomer.deps import DbSession
from shomer.models.jwk import JWK, JWKStatus

router = APIRouter()

#: Cache-Control max-age for the JWKS response (seconds).
JWKS_CACHE_MAX_AGE = 3600


@router.get("/.well-known/jwks.json")
async def jwks_endpoint(db: DbSession) -> JSONResponse:
    """Return the JWK Set containing all non-revoked public keys.

    Follows `RFC 7517 §5 <https://tools.ietf.org/html/rfc7517#section-5>`_.

    Parameters
    ----------
    db : DbSession
        Injected async database session.

    Returns
    -------
    JSONResponse
        JWK Set JSON with ``Cache-Control`` header.
    """
    stmt = select(JWK).where(JWK.status != JWKStatus.REVOKED)
    result = await db.execute(stmt)
    keys = result.scalars().all()

    jwk_set: dict[str, Any] = {
        "keys": [json.loads(k.public_key) for k in keys],
    }

    return JSONResponse(
        content=jwk_set,
        headers={
            "Cache-Control": f"public, max-age={JWKS_CACHE_MAX_AGE}",
        },
    )

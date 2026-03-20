# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Bearer token extraction per RFC 6750 §2.1.

Provides a FastAPI dependency that extracts the Bearer token from the
``Authorization`` header. Protected routes use this via ``BearerToken``::

    from shomer.deps import BearerToken

    @router.get("/protected")
    async def protected(token: BearerToken) -> dict: ...
"""

from __future__ import annotations

from fastapi import HTTPException, Request, status


async def extract_bearer_token(request: Request) -> str:
    """Extract the Bearer token from the Authorization header.

    Per RFC 6750 §2.1, the token is sent in the ``Authorization``
    request header field using the ``Bearer`` scheme.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.

    Returns
    -------
    str
        The raw Bearer token string.

    Raises
    ------
    HTTPException
        401 with ``WWW-Authenticate: Bearer`` if the header is missing,
        empty, or does not use the ``Bearer`` scheme.
    """
    auth_header = request.headers.get("authorization")

    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = auth_header.split(" ", 1)

    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header — expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1].strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empty Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token

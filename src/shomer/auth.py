# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unified authentication dependencies for protected routes.

Resolves the current user from a Bearer JWT token, a Personal Access
Token (``shm_pat_`` prefix), or a session cookie. Priority order:
Bearer JWT > PAT > Session.

Usage::

    from shomer.deps import CurrentUser, OptionalUser

    @router.get("/protected")
    async def protected(user: CurrentUser) -> dict:
        return {"user_id": str(user.user_id)}

    @router.get("/maybe-protected")
    async def maybe(user: OptionalUser) -> dict:
        if user is None:
            return {"anonymous": True}
        return {"user_id": str(user.user_id)}
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class CurrentUserInfo:
    """Authenticated user context for route handlers.

    Attributes
    ----------
    user_id : uuid.UUID
        The authenticated user's ID.
    scopes : list[str]
        OAuth2 scopes granted to the token (empty for session auth).
    tenant_id : uuid.UUID or None
        Tenant ID (None until multi-tenancy is implemented).
    auth_method : str
        How the user was authenticated (``bearer`` or ``session``).
    """

    user_id: uuid.UUID
    scopes: list[str] = field(default_factory=list)
    tenant_id: uuid.UUID | None = None
    auth_method: str = "bearer"


async def _try_bearer(request: Request, db: AsyncSession) -> CurrentUserInfo | None:
    """Try to authenticate via Bearer JWT token.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : AsyncSession
        Database session for access token lookup.

    Returns
    -------
    CurrentUserInfo or None
        The authenticated user if the Bearer token is valid.
    """
    auth_header = request.headers.get("authorization", "")
    if not auth_header.lower().startswith("bearer "):
        return None

    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        return None

    # Skip PAT tokens — they are handled by _try_pat
    from shomer.models.personal_access_token import PAT_PREFIX

    if token.startswith(PAT_PREFIX):
        return None

    # Check if the token's jti is in the access_tokens table (not revoked)

    # Decode JWT to get jti and sub
    import jwt as pyjwt
    from sqlalchemy import select

    from shomer.core.settings import get_settings
    from shomer.models.access_token import AccessToken

    settings = get_settings()
    try:
        payload = pyjwt.decode(
            token,
            settings.jwk_encryption_key or "dev-secret",
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except pyjwt.exceptions.PyJWTError:
        return None

    jti = payload.get("jti")
    sub = payload.get("sub")
    if not jti or not sub:
        return None

    # Verify token is not revoked
    stmt = select(AccessToken).where(
        AccessToken.jti == jti,
        AccessToken.revoked == False,  # noqa: E712
    )
    result = await db.execute(stmt)
    at = result.scalar_one_or_none()
    if at is None:
        return None

    scope_str = payload.get("scope", "")
    scopes = scope_str.split() if scope_str else []

    try:
        user_id = uuid.UUID(sub)
    except ValueError:
        # sub might be a client_id for client_credentials grants
        user_id = uuid.UUID(int=0)  # placeholder for M2M tokens

    return CurrentUserInfo(
        user_id=user_id,
        scopes=scopes,
        auth_method="bearer",
    )


async def _try_session(request: Request, db: AsyncSession) -> CurrentUserInfo | None:
    """Try to authenticate via session cookie.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : AsyncSession
        Database session for session lookup.

    Returns
    -------
    CurrentUserInfo or None
        The authenticated user if the session is valid.
    """
    session_token = request.cookies.get("session_id")
    if not session_token:
        return None

    from shomer.services.session_service import SessionService

    svc = SessionService(db)
    session = await svc.validate(session_token)
    if session is None:
        return None

    return CurrentUserInfo(
        user_id=session.user_id,
        scopes=[],
        auth_method="session",
    )


async def _try_pat(request: Request, db: AsyncSession) -> CurrentUserInfo | None:
    """Try to authenticate via Personal Access Token.

    Detects PATs by the ``shm_pat_`` prefix in the Bearer token.
    Validates the token, updates last_used_at, and returns user context.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : AsyncSession
        Database session.

    Returns
    -------
    CurrentUserInfo or None
        The authenticated user if the PAT is valid.
    """
    auth_header = request.headers.get("authorization", "")
    if not auth_header.lower().startswith("bearer "):
        return None

    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        return None

    from shomer.models.personal_access_token import PAT_PREFIX

    if not token.startswith(PAT_PREFIX):
        return None

    from shomer.services.pat_service import PATError, PATService

    svc = PATService(db)
    try:
        client_ip = request.client.host if request.client else None
        pat = await svc.validate(token, client_ip=client_ip)
    except PATError:
        return None

    scopes = pat.scopes.split() if pat.scopes else []

    return CurrentUserInfo(
        user_id=pat.user_id,
        scopes=scopes,
        auth_method="pat",
    )


async def resolve_current_user(
    request: Request, db: AsyncSession
) -> CurrentUserInfo | None:
    """Resolve the current user from Bearer JWT, PAT, or session cookie.

    Priority: Bearer JWT > PAT > Session.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : AsyncSession
        Database session.

    Returns
    -------
    CurrentUserInfo or None
        The authenticated user, or None if unauthenticated.
    """
    # Try Bearer JWT first
    user = await _try_bearer(request, db)
    if user is not None:
        return user

    # Try PAT
    user = await _try_pat(request, db)
    if user is not None:
        return user

    # Fall back to session
    return await _try_session(request, db)


async def get_current_user(request: Request, db: AsyncSession) -> CurrentUserInfo:
    """FastAPI dependency: require an authenticated user.

    Tries Bearer JWT first, then session cookie. Raises 401 if neither
    provides a valid identity.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : AsyncSession
        Database session (injected via Depends).

    Returns
    -------
    CurrentUserInfo
        The authenticated user.

    Raises
    ------
    HTTPException
        401 if no valid authentication is found.
    """
    user = await resolve_current_user(request, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_optional_user(
    request: Request, db: AsyncSession
) -> CurrentUserInfo | None:
    """FastAPI dependency: optionally resolve the current user.

    Like :func:`get_current_user` but returns ``None`` instead of 401.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : AsyncSession
        Database session (injected via Depends).

    Returns
    -------
    CurrentUserInfo or None
        The authenticated user, or None.
    """
    return await resolve_current_user(request, db)

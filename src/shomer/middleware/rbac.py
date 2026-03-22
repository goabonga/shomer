# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""RBAC authorization dependencies for route-level access control.

Provides ``require_scope`` and ``require_any_scope`` dependency factories
that check the current user's permissions via :class:`RBACService`.

Usage::

    from shomer.middleware.rbac import require_scope

    @router.get("/admin/users", dependencies=[Depends(require_scope("admin:users:read"))])
    async def list_users() -> dict: ...

    # Or with require_any_scope:
    @router.post("/content", dependencies=[Depends(require_any_scope(["editor:write", "admin:*"]))])
    async def create_content() -> dict: ...
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from shomer.auth import CurrentUserInfo
from shomer.deps import get_db


def require_scope(scope: str) -> Callable[..., Coroutine[Any, Any, None]]:
    """Create a dependency that requires a specific RBAC scope.

    Parameters
    ----------
    scope : str
        The required scope (e.g. ``admin:users:read``).

    Returns
    -------
    Callable
        A FastAPI dependency that raises 403 if the user lacks the scope.

    Examples
    --------
    ::

        @router.get("/admin", dependencies=[Depends(require_scope("admin:read"))])
        async def admin_page() -> dict: ...
    """

    async def _check(
        request: Request,
        db: AsyncSession = Depends(get_db),  # noqa: B008
    ) -> None:
        user = await _resolve_user(request, db)
        from shomer.services.rbac_service import RBACService

        svc = RBACService(db)
        has = await svc.has_permission(
            user_id=user.user_id,
            scope=scope,
            tenant_id=user.tenant_id,
        )
        if not has:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required scope: {scope}",
            )

    return _check


def require_any_scope(scopes: list[str]) -> Callable[..., Coroutine[Any, Any, None]]:
    """Create a dependency that requires at least one of the given scopes.

    Parameters
    ----------
    scopes : list[str]
        Required scopes (at least one must match).

    Returns
    -------
    Callable
        A FastAPI dependency that raises 403 if the user lacks all scopes.

    Examples
    --------
    ::

        @router.post("/content", dependencies=[Depends(require_any_scope(["editor:write", "admin:*"]))])
        async def create() -> dict: ...
    """

    async def _check(
        request: Request,
        db: AsyncSession = Depends(get_db),  # noqa: B008
    ) -> None:
        user = await _resolve_user(request, db)
        from shomer.services.rbac_service import RBACService

        svc = RBACService(db)
        has = await svc.has_any_permission(
            user_id=user.user_id,
            scopes=scopes,
            tenant_id=user.tenant_id,
        )
        if not has:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required one of: {', '.join(scopes)}",
            )

    return _check


async def _resolve_user(request: Request, db: AsyncSession) -> CurrentUserInfo:
    """Resolve the current authenticated user.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : AsyncSession
        Database session.

    Returns
    -------
    CurrentUserInfo
        The authenticated user context.

    Raises
    ------
    HTTPException
        401 if no user is authenticated.
    """
    from shomer.auth import get_current_user

    return await get_current_user(request, db)

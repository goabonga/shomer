# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""FastAPI dependency injection helpers.

This module centralises all ``Depends()`` callables used by route handlers.
Import the ``Annotated`` type aliases to keep route signatures concise::

    from shomer.deps import DbSession, Config

    @router.get("/example")
    async def example(db: DbSession, config: Config) -> dict: ...
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import Annotated, Any

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from shomer.core.database import async_session
from shomer.core.settings import Settings, get_settings


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield an async database session.

    The session is committed on success and rolled back on exception.
    Intended for use with ``Depends(get_db)``.

    Yields
    ------
    AsyncSession
        An async SQLAlchemy session.
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_config() -> Settings:
    """Return the cached application settings.

    Returns
    -------
    Settings
        The application configuration singleton.
    """
    return get_settings()


async def get_current_tenant(request: Request) -> uuid.UUID | None:
    """Resolve the current tenant from the request state.

    The tenant is resolved by :class:`TenantMiddleware` and stored
    on ``request.state.tenant_id``.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.

    Returns
    -------
    uuid.UUID or None
        The tenant ID, or ``None`` when no tenant is resolved.
    """
    return getattr(request.state, "tenant_id", None)


#: Annotated type for an injected async DB session.
DbSession = Annotated[AsyncSession, Depends(get_db)]

#: Annotated type for injected application settings.
Config = Annotated[Settings, Depends(get_config)]

#: Annotated type for the current tenant ID (may be None).
TenantId = Annotated[uuid.UUID | None, Depends(get_current_tenant)]


async def get_bearer_token(request: Request) -> str:  # pragma: no cover
    """Extract Bearer token from the Authorization header.

    Delegates to :func:`shomer.middleware.bearer.extract_bearer_token`.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.

    Returns
    -------
    str
        The raw Bearer token.

    Raises
    ------
    HTTPException
        401 with ``WWW-Authenticate: Bearer`` if absent or malformed.
    """
    from shomer.middleware.bearer import extract_bearer_token

    return await extract_bearer_token(request)


#: Annotated type for an extracted Bearer token from the Authorization header.
BearerToken = Annotated[str, Depends(get_bearer_token)]


async def _get_current_user(  # pragma: no cover
    request: Request,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Any:
    """Dependency wrapper for :func:`shomer.auth.get_current_user`."""
    from shomer.auth import get_current_user as _get_user

    return await _get_user(request, db)


async def _get_optional_user(  # pragma: no cover
    request: Request,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Any:
    """Dependency wrapper for :func:`shomer.auth.get_optional_user`."""
    from shomer.auth import get_optional_user as _get_opt

    return await _get_opt(request, db)


from shomer.auth import CurrentUserInfo  # noqa: E402

#: Annotated type for a required authenticated user.
CurrentUser = Annotated[CurrentUserInfo, Depends(_get_current_user)]

#: Annotated type for an optionally authenticated user (None if anonymous).
OptionalUser = Annotated[CurrentUserInfo | None, Depends(_get_optional_user)]

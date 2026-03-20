# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Token introspection service per RFC 7662."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shomer.models.access_token import AccessToken
from shomer.models.refresh_token import RefreshToken


class IntrospectionService:
    """Introspect access and refresh tokens.

    Returns metadata about the token including its active status.

    Attributes
    ----------
    session : AsyncSession
        Database session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def introspect(
        self,
        *,
        token: str,
        token_type_hint: str | None = None,
    ) -> dict[str, Any]:
        """Introspect a token and return its metadata.

        Parameters
        ----------
        token : str
            The token value to introspect.
        token_type_hint : str or None
            ``access_token`` or ``refresh_token``.

        Returns
        -------
        dict[str, Any]
            RFC 7662 introspection response with ``active`` field.
        """
        if token_type_hint == "refresh_token":
            return await self._introspect_refresh_token(token)
        if token_type_hint == "access_token":
            return await self._introspect_access_token(token)

        # No hint: try access first (more common for introspection)
        result = await self._introspect_access_token(token)
        if result["active"]:
            return result
        return await self._introspect_refresh_token(token)

    async def _introspect_access_token(self, token: str) -> dict[str, Any]:
        """Introspect an access token JWT.

        Parameters
        ----------
        token : str
            The JWT access token.

        Returns
        -------
        dict[str, Any]
            Introspection response.
        """
        import jwt as pyjwt

        from shomer.core.settings import get_settings

        settings = get_settings()
        try:
            payload = pyjwt.decode(
                token,
                settings.jwk_encryption_key or "dev-secret",
                algorithms=["HS256"],
                options={"verify_aud": False, "verify_exp": False},
            )
        except pyjwt.exceptions.PyJWTError:
            return {"active": False}

        jti = payload.get("jti")
        if not jti:
            return {"active": False}

        # Check if revoked
        stmt = select(AccessToken).where(AccessToken.jti == jti)
        result = await self.session.execute(stmt)
        at = result.scalar_one_or_none()

        if at is None or at.revoked:
            return {"active": False}

        # Check expiration
        now = datetime.now(timezone.utc)
        expires_at = at.expires_at
        if expires_at.tzinfo is None:  # pragma: no cover
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < now:
            return {"active": False}

        return {
            "active": True,
            "scope": payload.get("scope", ""),
            "client_id": at.client_id,
            "token_type": "Bearer",
            "exp": int(expires_at.timestamp()),
            "iat": payload.get("iat"),
            "sub": payload.get("sub"),
            "aud": payload.get("aud"),
            "iss": payload.get("iss"),
        }

    async def _introspect_refresh_token(self, token: str) -> dict[str, Any]:
        """Introspect a refresh token.

        Parameters
        ----------
        token : str
            The raw refresh token.

        Returns
        -------
        dict[str, Any]
            Introspection response.
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.session.execute(stmt)
        rt = result.scalar_one_or_none()

        if rt is None or rt.revoked:
            return {"active": False}

        now = datetime.now(timezone.utc)
        expires_at = rt.expires_at
        if expires_at.tzinfo is None:  # pragma: no cover
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < now:
            return {"active": False}

        return {
            "active": True,
            "scope": rt.scopes,
            "client_id": rt.client_id,
            "token_type": "refresh_token",
            "exp": int(expires_at.timestamp()),
            "sub": str(rt.user_id),
        }

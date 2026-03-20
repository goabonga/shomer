# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Token revocation service per RFC 7009."""

from __future__ import annotations

import hashlib

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from shomer.models.access_token import AccessToken
from shomer.models.refresh_token import RefreshToken


class RevocationService:
    """Revoke access and refresh tokens.

    Per RFC 7009, revocation is best-effort: if the token is unknown
    or already revoked, no error is raised.

    Attributes
    ----------
    session : AsyncSession
        Database session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def revoke(
        self,
        *,
        token: str,
        token_type_hint: str | None = None,
        client_id: str,
    ) -> None:
        """Revoke a token.

        Parameters
        ----------
        token : str
            The token value to revoke.
        token_type_hint : str or None
            ``access_token`` or ``refresh_token``. If None, tries both.
        client_id : str
            The authenticated client ID (must match the token's client).
        """
        if token_type_hint == "refresh_token":
            await self._revoke_refresh_token(token, client_id)
        elif token_type_hint == "access_token":
            await self._revoke_access_token(token, client_id)
        else:
            # Try refresh first (more common), then access
            revoked = await self._revoke_refresh_token(token, client_id)
            if not revoked:
                await self._revoke_access_token(token, client_id)

    async def _revoke_refresh_token(self, token: str, client_id: str) -> bool:
        """Revoke a refresh token and its entire family.

        Parameters
        ----------
        token : str
            The raw refresh token.
        client_id : str
            Client that owns the token.

        Returns
        -------
        bool
            True if a token was found and revoked.
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        stmt = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.client_id == client_id,
        )
        result = await self.session.execute(stmt)
        rt = result.scalar_one_or_none()

        if rt is None:
            return False

        # Revoke entire family
        family_stmt = (
            update(RefreshToken)
            .where(RefreshToken.family_id == rt.family_id)
            .values(revoked=True)
        )
        await self.session.execute(family_stmt)
        await self.session.flush()
        return True

    async def _revoke_access_token(self, token: str, client_id: str) -> bool:
        """Revoke an access token by its JWT value.

        Decodes the JWT to extract the jti, then marks the token as revoked.

        Parameters
        ----------
        token : str
            The JWT access token.
        client_id : str
            Client that owns the token.

        Returns
        -------
        bool
            True if a token was found and revoked.
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
            return False

        jti = payload.get("jti")
        if not jti:
            return False

        stmt = select(AccessToken).where(
            AccessToken.jti == jti,
            AccessToken.client_id == client_id,
        )
        result = await self.session.execute(stmt)
        at = result.scalar_one_or_none()

        if at is None:
            return False

        at.revoked = True
        await self.session.flush()
        return True

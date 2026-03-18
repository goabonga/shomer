# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""JWT creation service using RS256."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from sqlalchemy.ext.asyncio import AsyncSession

from shomer.core.security import AESEncryption
from shomer.core.settings import Settings
from shomer.services.jwk_service import JWKService


class JWTService:
    """Create signed JWTs (access tokens and ID tokens) using the active RSA key.

    Attributes
    ----------
    settings : Settings
        Application configuration.
    jwk_service : JWKService
        Key management service for retrieving the active signing key.
    encryption : AESEncryption
        Cipher for decrypting private key material.
    """

    def __init__(
        self,
        settings: Settings,
        session: AsyncSession,
        encryption: AESEncryption,
    ) -> None:
        self.settings = settings
        self.encryption = encryption
        self.jwk_service = JWKService(
            session, encryption, key_size=settings.rsa_key_size
        )

    async def create_access_token(
        self,
        *,
        sub: str,
        aud: str | list[str],
        scopes: list[str] | None = None,
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        """Create a signed access token.

        Parameters
        ----------
        sub : str
            Subject identifier (user ID).
        aud : str or list[str]
            Audience claim.
        scopes : list[str] or None
            OAuth2 scopes to embed in the ``scope`` claim.
        extra_claims : dict[str, Any] or None
            Additional claims to include.

        Returns
        -------
        str
            Encoded JWT string.

        Raises
        ------
        RuntimeError
            If no active signing key exists.
        """
        claims: dict[str, Any] = {}
        if scopes:
            claims["scope"] = " ".join(scopes)
        if extra_claims:
            claims.update(extra_claims)

        return await self._sign(
            sub=sub,
            aud=aud,
            exp_seconds=self.settings.jwt_access_token_exp,
            extra_claims=claims,
            token_type="access_token",
        )

    async def create_id_token(
        self,
        *,
        sub: str,
        aud: str | list[str],
        nonce: str | None = None,
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        """Create a signed OIDC ID token.

        Parameters
        ----------
        sub : str
            Subject identifier (user ID).
        aud : str or list[str]
            Audience claim (client_id).
        nonce : str or None
            Nonce from the authorization request.
        extra_claims : dict[str, Any] or None
            Additional OIDC claims (name, email, etc.).

        Returns
        -------
        str
            Encoded JWT string.

        Raises
        ------
        RuntimeError
            If no active signing key exists.
        """
        claims: dict[str, Any] = {}
        if nonce:
            claims["nonce"] = nonce
        if extra_claims:
            claims.update(extra_claims)

        return await self._sign(
            sub=sub,
            aud=aud,
            exp_seconds=self.settings.jwt_id_token_exp,
            extra_claims=claims,
            token_type="id_token",
        )

    async def _sign(
        self,
        *,
        sub: str,
        aud: str | list[str],
        exp_seconds: int,
        extra_claims: dict[str, Any],
        token_type: str,
    ) -> str:
        """Build and sign a JWT with standard claims.

        Parameters
        ----------
        sub : str
            Subject identifier.
        aud : str or list[str]
            Audience claim.
        exp_seconds : int
            Token lifetime in seconds.
        extra_claims : dict[str, Any]
            Extra claims merged into the payload.
        token_type : str
            Token type hint (for future extensibility).

        Returns
        -------
        str
            Signed JWT.

        Raises
        ------
        RuntimeError
            If no active signing key is available.
        """
        active_key = await self.jwk_service.get_active_signing_key()
        if active_key is None:
            raise RuntimeError("No active signing key available")

        now = datetime.now(timezone.utc)
        payload: dict[str, Any] = {
            "iss": self.settings.jwt_issuer,
            "sub": sub,
            "aud": aud,
            "exp": now + timedelta(seconds=exp_seconds),
            "iat": now,
            "jti": uuid.uuid4().hex,
            **extra_claims,
        }

        # Decrypt private key
        private_pem = self.encryption.decrypt(active_key.private_key_enc)
        private_key = load_pem_private_key(private_pem, password=None)

        return jwt.encode(
            payload,
            private_key,  # type: ignore[arg-type]
            algorithm=active_key.algorithm,
            headers={"kid": active_key.kid},
        )

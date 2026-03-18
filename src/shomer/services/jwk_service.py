# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""RSA key lifecycle management service."""

from __future__ import annotations

import json
import uuid

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from shomer.core.security import AESEncryption
from shomer.models.jwk import JWK, JWKStatus


class JWKService:
    """Manage the lifecycle of RSA signing keys.

    Attributes
    ----------
    session : AsyncSession
        Database session.
    encryption : AESEncryption
        AES-256-GCM cipher for private key encryption.
    key_size : int
        RSA key size in bits.
    """

    def __init__(
        self,
        session: AsyncSession,
        encryption: AESEncryption,
        *,
        key_size: int = 2048,
    ) -> None:
        self.session = session
        self.encryption = encryption
        self.key_size = key_size

    async def generate_key(self, *, algorithm: str = "RS256") -> JWK:
        """Generate a new RSA key pair and persist it.

        Any existing active key is moved to rotated status first
        so there is always at most one active signing key.

        Parameters
        ----------
        algorithm : str
            JWA algorithm identifier (default ``RS256``).

        Returns
        -------
        JWK
            The newly created active key.
        """
        # Rotate any currently active key
        await self._rotate_active_keys()

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=self.key_size,
        )

        # Serialize private key to PEM, then encrypt
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        private_key_enc = self.encryption.encrypt(private_pem)

        # Serialize public key to JWK JSON
        public_key = private_key.public_key()
        public_numbers = public_key.public_numbers()
        n_bytes = public_numbers.n.to_bytes(
            (public_numbers.n.bit_length() + 7) // 8, byteorder="big"
        )
        e_bytes = public_numbers.e.to_bytes(
            (public_numbers.e.bit_length() + 7) // 8, byteorder="big"
        )

        kid = f"shomer-{uuid.uuid4().hex[:12]}"

        import base64

        pub_jwk = json.dumps(
            {
                "kty": "RSA",
                "kid": kid,
                "alg": algorithm,
                "use": "sig",
                "n": base64.urlsafe_b64encode(n_bytes).rstrip(b"=").decode(),
                "e": base64.urlsafe_b64encode(e_bytes).rstrip(b"=").decode(),
            }
        )

        jwk = JWK(
            kid=kid,
            algorithm=algorithm,
            public_key=pub_jwk,
            private_key_enc=private_key_enc,
            status=JWKStatus.ACTIVE,
        )
        self.session.add(jwk)
        await self.session.flush()
        return jwk

    async def rotate(self) -> JWK:
        """Rotate the active key: mark it as rotated and generate a new one.

        The rotated key remains available for signature verification
        (grace period) until explicitly revoked.

        Returns
        -------
        JWK
            The new active key.
        """
        return await self.generate_key()

    async def revoke(self, kid: str) -> JWK | None:
        """Revoke a key by its kid.

        Parameters
        ----------
        kid : str
            Key ID to revoke.

        Returns
        -------
        JWK or None
            The revoked key, or ``None`` if not found.
        """
        stmt = select(JWK).where(JWK.kid == kid)
        result = await self.session.execute(stmt)
        jwk = result.scalar_one_or_none()
        if jwk is None:
            return None
        jwk.status = JWKStatus.REVOKED
        await self.session.flush()
        return jwk

    async def get_active_signing_key(self) -> JWK | None:
        """Return the single active signing key.

        Returns
        -------
        JWK or None
            The active key, or ``None`` if no key is active.
        """
        stmt = select(JWK).where(JWK.status == JWKStatus.ACTIVE)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_public_keys(self) -> list[JWK]:
        """Return all non-revoked keys for the JWKS endpoint.

        Returns
        -------
        list[JWK]
            Active and rotated keys (excludes revoked).
        """
        stmt = select(JWK).where(JWK.status != JWKStatus.REVOKED)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def _rotate_active_keys(self) -> None:
        """Move all active keys to rotated status."""
        stmt = (
            update(JWK)
            .where(JWK.status == JWKStatus.ACTIVE)
            .values(status=JWKStatus.ROTATED)
        )
        await self.session.execute(stmt)

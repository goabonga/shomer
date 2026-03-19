# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""JWT validation service with signature verification and claims checking."""

from __future__ import annotations

import enum
import json
from dataclasses import dataclass
from typing import Any

import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shomer.core.settings import Settings
from shomer.models.jwk import JWK, JWKStatus


class TokenError(enum.Enum):
    """Specific error codes for JWT validation failures.

    Attributes
    ----------
    EXPIRED
        The token has expired.
    INVALID_SIGNATURE
        The signature does not match any known key.
    INVALID_CLAIMS
        Required claims are missing or invalid (iss, aud).
    KEY_NOT_FOUND
        The ``kid`` in the token header does not match any non-revoked key.
    DECODE_ERROR
        The token is malformed or cannot be decoded.
    """

    EXPIRED = "expired"
    INVALID_SIGNATURE = "invalid_signature"
    INVALID_CLAIMS = "invalid_claims"
    KEY_NOT_FOUND = "key_not_found"
    DECODE_ERROR = "decode_error"


@dataclass(frozen=True)
class TokenValidationResult:
    """Result of a JWT validation attempt.

    Attributes
    ----------
    valid : bool
        Whether the token is valid.
    claims : dict[str, Any] or None
        Decoded claims if valid, ``None`` otherwise.
    error : TokenError or None
        Error code if invalid, ``None`` otherwise.
    error_message : str
        Human-readable error description.
    """

    valid: bool
    claims: dict[str, Any] | None = None
    error: TokenError | None = None
    error_message: str = ""


class JWTValidationService:
    """Validate JWTs using RS256 with kid-based key lookup.

    Attributes
    ----------
    settings : Settings
        Application configuration.
    session : AsyncSession
        Database session for key lookup.
    """

    def __init__(self, settings: Settings, session: AsyncSession) -> None:
        self.settings = settings
        self.session = session

    async def validate(
        self,
        token: str,
        *,
        audience: str | list[str] | None = None,
    ) -> TokenValidationResult:
        """Validate a JWT token.

        Performs kid-based key lookup, RS256 signature verification,
        and claims validation (iss, aud, exp, nbf) with configurable
        clock skew tolerance.

        Parameters
        ----------
        token : str
            Encoded JWT string.
        audience : str or list[str] or None
            Expected audience. If ``None``, audience is not checked.

        Returns
        -------
        TokenValidationResult
            Validation result with claims or error details.
        """
        # Extract kid from header
        try:
            header = jwt.get_unverified_header(token)
        except jwt.exceptions.DecodeError:
            return TokenValidationResult(
                valid=False,
                error=TokenError.DECODE_ERROR,
                error_message="Token is malformed",
            )

        kid = header.get("kid")
        if not kid:
            return TokenValidationResult(
                valid=False,
                error=TokenError.KEY_NOT_FOUND,
                error_message="Token header missing kid",
            )

        # Look up key by kid (active or rotated)
        public_key = await self._get_public_key(kid)
        if public_key is None:
            return TokenValidationResult(
                valid=False,
                error=TokenError.KEY_NOT_FOUND,
                error_message=f"No non-revoked key found for kid={kid}",
            )

        # Verify signature and decode claims
        decode_options: dict[str, Any] = {}
        decode_kwargs: dict[str, Any] = {
            "algorithms": ["RS256"],
            "issuer": self.settings.jwt_issuer,
            "leeway": self.settings.jwt_clock_skew,
            "options": decode_options,
        }
        if audience is not None:
            decode_kwargs["audience"] = audience
        else:
            decode_options["verify_aud"] = False

        try:
            claims = jwt.decode(token, public_key, **decode_kwargs)
        except jwt.ExpiredSignatureError:
            return TokenValidationResult(
                valid=False,
                error=TokenError.EXPIRED,
                error_message="Token has expired",
            )
        except jwt.InvalidSignatureError:
            return TokenValidationResult(
                valid=False,
                error=TokenError.INVALID_SIGNATURE,
                error_message="Invalid token signature",
            )
        except (jwt.InvalidIssuerError, jwt.InvalidAudienceError) as exc:
            return TokenValidationResult(
                valid=False,
                error=TokenError.INVALID_CLAIMS,
                error_message=str(exc),
            )
        except jwt.DecodeError:  # pragma: no cover
            return TokenValidationResult(
                valid=False,
                error=TokenError.DECODE_ERROR,
                error_message="Token decode failed",
            )

        return TokenValidationResult(valid=True, claims=claims)

    async def _get_public_key(self, kid: str) -> Any:
        """Look up a public key by kid from non-revoked keys.

        Parameters
        ----------
        kid : str
            Key ID from the JWT header.

        Returns
        -------
        RSAPublicKey or None
            The public key object, or ``None`` if not found.
        """
        stmt = select(JWK).where(
            JWK.kid == kid,
            JWK.status != JWKStatus.REVOKED,
        )
        result = await self.session.execute(stmt)
        jwk = result.scalar_one_or_none()
        if jwk is None:
            return None

        pub_jwk = json.loads(jwk.public_key)
        return jwt.algorithms.RSAAlgorithm.from_jwk(pub_jwk)

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Token Exchange service per RFC 8693."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from shomer.core.settings import Settings
from shomer.services.jwt_validation_service import JWTValidationService, TokenError


class TokenExchangeError(Exception):
    """Raised when a token exchange request fails.

    Attributes
    ----------
    error : str
        OAuth2 error code.
    description : str
        Human-readable error description.
    """

    def __init__(self, error: str, description: str) -> None:
        self.error = error
        self.description = description
        super().__init__(description)


class TokenType(str, enum.Enum):
    """Token type identifiers per RFC 8693 §3.

    Attributes
    ----------
    ACCESS_TOKEN
        An OAuth 2.0 access token.
    REFRESH_TOKEN
        An OAuth 2.0 refresh token.
    ID_TOKEN
        An OpenID Connect ID token.
    JWT
        A JWT token (generic).
    """

    ACCESS_TOKEN = "urn:ietf:params:oauth:token-type:access_token"
    REFRESH_TOKEN = "urn:ietf:params:oauth:token-type:refresh_token"
    ID_TOKEN = "urn:ietf:params:oauth:token-type:id_token"
    JWT = "urn:ietf:params:oauth:token-type:jwt"


@dataclass(frozen=True)
class ExchangeRequest:
    """Parsed token exchange request per RFC 8693 §2.1.

    Attributes
    ----------
    subject_token : str
        The token to exchange.
    subject_token_type : TokenType
        Type of the subject token.
    actor_token : str or None
        Optional actor token for delegation.
    actor_token_type : TokenType or None
        Type of the actor token.
    requested_token_type : TokenType
        Desired type of the issued token.
    scope : str or None
        Requested scopes for the new token.
    audience : str or None
        Target audience for the new token.
    """

    subject_token: str
    subject_token_type: TokenType
    actor_token: str | None = None
    actor_token_type: TokenType | None = None
    requested_token_type: TokenType = TokenType.ACCESS_TOKEN
    scope: str | None = None
    audience: str | None = None


@dataclass
class ExchangeResult:
    """Result of a successful token exchange.

    Attributes
    ----------
    subject : str
        The ``sub`` claim from the validated subject token.
    scopes : list[str]
        Computed scopes for the new token.
    audience : str
        Target audience for the new token.
    act : dict[str, str] or None
        Actor claim for delegation (``{"sub": "<actor_sub>"}``).
    """

    subject: str
    scopes: list[str] = field(default_factory=list)
    audience: str = ""
    act: dict[str, str] | None = None


#: Grant type URI for token exchange per RFC 8693.
TOKEN_EXCHANGE_GRANT = "urn:ietf:params:oauth:grant-type:token-exchange"


class TokenExchangeService:
    """Validate and process token exchange requests per RFC 8693.

    Validates subject and actor tokens, checks client permissions,
    computes scopes (intersection of requested vs allowed), and
    supports impersonation and delegation flows.

    Attributes
    ----------
    settings : Settings
        Application configuration.
    session : AsyncSession
        Database session.
    jwt_validation : JWTValidationService
        JWT validation service for token verification.
    """

    def __init__(self, settings: Settings, session: AsyncSession) -> None:
        self.settings = settings
        self.session = session
        self.jwt_validation = JWTValidationService(settings, session)

    async def validate_exchange(
        self,
        *,
        request: ExchangeRequest,
        client_id: str,
        client_grant_types: list[str],
        client_scopes: list[str],
    ) -> ExchangeResult:
        """Validate a token exchange request and compute the result.

        Parameters
        ----------
        request : ExchangeRequest
            The parsed exchange request.
        client_id : str
            The authenticated client's identifier.
        client_grant_types : list[str]
            Grant types allowed for the client.
        client_scopes : list[str]
            Scopes allowed for the client.

        Returns
        -------
        ExchangeResult
            The validated exchange result with subject, scopes, and
            optional actor claim.

        Raises
        ------
        TokenExchangeError
            If validation fails at any step.
        """
        # 1. Check client is authorized for token exchange
        self._check_client_permission(client_grant_types)

        # 2. Validate subject token
        subject_claims = await self._validate_subject_token(request)

        # 3. Compute scopes
        scopes = self._compute_scopes(
            requested=request.scope,
            subject_scopes=subject_claims.get("scope", ""),
            client_scopes=client_scopes,
        )

        # 4. Determine audience
        audience = request.audience or client_id

        # 5. Handle delegation (actor token present)
        act: dict[str, str] | None = None
        if request.actor_token:
            act = await self._validate_actor_token(request)

        subject = subject_claims.get("sub", "")
        if not subject:
            raise TokenExchangeError(
                "invalid_request", "Subject token missing sub claim"
            )

        return ExchangeResult(
            subject=subject,
            scopes=scopes,
            audience=audience,
            act=act,
        )

    def _check_client_permission(self, client_grant_types: list[str]) -> None:
        """Verify the client is authorized for token exchange.

        Parameters
        ----------
        client_grant_types : list[str]
            Grant types allowed for the client.

        Raises
        ------
        TokenExchangeError
            If token exchange is not in the client's allowed grants.
        """
        if TOKEN_EXCHANGE_GRANT not in client_grant_types:
            raise TokenExchangeError(
                "unauthorized_client",
                "Client is not authorized for token exchange",
            )

    async def _validate_subject_token(self, request: ExchangeRequest) -> dict[str, Any]:
        """Validate the subject token via JWT verification.

        Tries HS256 verification first (server-issued tokens), then
        falls back to RS256 kid-based validation via JWTValidationService.

        Parameters
        ----------
        request : ExchangeRequest
            The exchange request containing the subject token.

        Returns
        -------
        dict[str, Any]
            The validated claims from the subject token.

        Raises
        ------
        TokenExchangeError
            If the subject token is invalid.
        """
        import jwt as pyjwt

        # Try HS256 first (server-issued tokens)
        secret = self.settings.jwk_encryption_key or "dev-secret"
        try:
            claims: dict[str, Any] = pyjwt.decode(
                request.subject_token,
                secret,
                algorithms=["HS256"],
                issuer=self.settings.jwt_issuer,
                options={"verify_aud": False},
            )
            return claims
        except pyjwt.exceptions.PyJWTError:
            pass

        # Fall back to RS256 kid-based validation
        result = await self.jwt_validation.validate(request.subject_token)

        if not result.valid:
            error_map = {
                TokenError.EXPIRED: "Subject token has expired",
                TokenError.INVALID_SIGNATURE: "Subject token has invalid signature",
                TokenError.INVALID_CLAIMS: "Subject token has invalid claims",
                TokenError.KEY_NOT_FOUND: "Subject token key not found",
                TokenError.DECODE_ERROR: "Subject token is malformed",
            }
            msg = error_map.get(result.error, result.error_message)  # type: ignore[arg-type]
            raise TokenExchangeError("invalid_grant", msg)

        return result.claims or {}

    def _compute_scopes(
        self,
        *,
        requested: str | None,
        subject_scopes: str,
        client_scopes: list[str],
    ) -> list[str]:
        """Compute the resulting scopes for the exchanged token.

        The result is the intersection of requested scopes, subject token
        scopes, and client allowed scopes. If no scopes are requested,
        the subject token's scopes are used (filtered by client allowlist).

        Parameters
        ----------
        requested : str or None
            Space-separated requested scopes.
        subject_scopes : str
            Space-separated scopes from the subject token.
        client_scopes : list[str]
            Scopes allowed for the client.

        Returns
        -------
        list[str]
            The computed scopes.
        """
        subject_set = set(subject_scopes.split()) if subject_scopes else set()
        client_set = set(client_scopes)

        if requested:
            requested_set = set(requested.split())
            # Intersection of all three: requested ∩ subject ∩ client
            return sorted(requested_set & subject_set & client_set)

        # No scope requested: use subject scopes filtered by client allowlist
        return sorted(subject_set & client_set)

    async def _validate_actor_token(self, request: ExchangeRequest) -> dict[str, str]:
        """Validate the actor token for delegation flows.

        Parameters
        ----------
        request : ExchangeRequest
            The exchange request containing the actor token.

        Returns
        -------
        dict[str, str]
            The ``act`` claim (``{"sub": "<actor_sub>"}``).

        Raises
        ------
        TokenExchangeError
            If the actor token is invalid or missing sub claim.
        """
        if not request.actor_token:
            raise TokenExchangeError(
                "invalid_request", "actor_token is required for delegation"
            )

        if request.actor_token_type is None:
            raise TokenExchangeError(
                "invalid_request",
                "actor_token_type is required when actor_token is provided",
            )

        # Try HS256 first (server-issued tokens)
        import jwt as pyjwt

        secret = self.settings.jwk_encryption_key or "dev-secret"
        actor_claims: dict[str, Any] | None = None
        try:
            actor_claims = pyjwt.decode(
                request.actor_token,
                secret,
                algorithms=["HS256"],
                issuer=self.settings.jwt_issuer,
                options={"verify_aud": False},
            )
        except pyjwt.exceptions.PyJWTError:
            pass

        if actor_claims is None:
            result = await self.jwt_validation.validate(request.actor_token)
            if not result.valid:
                raise TokenExchangeError(
                    "invalid_grant",
                    f"Actor token is invalid: {result.error_message}",
                )
            actor_claims = result.claims or {}

        actor_sub = actor_claims.get("sub")
        if not actor_sub:
            raise TokenExchangeError("invalid_grant", "Actor token missing sub claim")

        return {"sub": actor_sub}

    @staticmethod
    def parse_token_type(token_type: str | None) -> TokenType | None:
        """Parse a token type URI to a TokenType enum.

        Parameters
        ----------
        token_type : str or None
            The token type URI string.

        Returns
        -------
        TokenType or None
            The parsed token type, or ``None`` if the input is empty.

        Raises
        ------
        TokenExchangeError
            If the token type URI is not recognized.
        """
        if not token_type:
            return None
        try:
            return TokenType(token_type)
        except ValueError:
            raise TokenExchangeError(
                "invalid_request",
                f"Unsupported token type: {token_type}",
            )

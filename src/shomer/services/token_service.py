# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""OAuth2 token endpoint service (RFC 6749 §4.1.3 and §4.4)."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shomer.core.settings import Settings
from shomer.models.access_token import AccessToken
from shomer.models.authorization_code import AuthorizationCode
from shomer.models.refresh_token import RefreshToken


class TokenError(Exception):
    """OAuth2 token error per RFC 6749 §5.2.

    Attributes
    ----------
    error : str
        Error code.
    description : str
        Human-readable description.
    """

    def __init__(self, error: str, description: str) -> None:
        self.error = error
        self.description = description
        super().__init__(description)


@dataclass
class TokenResponse:
    """OAuth2 token response per RFC 6749 §5.1.

    Attributes
    ----------
    access_token : str
        The access token (JWT).
    token_type : str
        Always ``Bearer``.
    expires_in : int
        Token lifetime in seconds.
    refresh_token : str or None
        The refresh token (opaque).
    scope : str
        Granted scopes.
    id_token : str or None
        OIDC ID token (JWT) if ``openid`` scope was requested.
    """

    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    refresh_token: str | None = None
    scope: str = ""
    id_token: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to RFC 6749 §5.1 response dict."""
        result: dict[str, Any] = {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
        }
        if self.refresh_token:
            result["refresh_token"] = self.refresh_token
        if self.scope:
            result["scope"] = self.scope
        if self.id_token:
            result["id_token"] = self.id_token
        return result


class TokenService:
    """Exchange authorization codes or client credentials for tokens.

    Attributes
    ----------
    session : AsyncSession
        Database session.
    settings : Settings
        Application settings.
    """

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    async def exchange_authorization_code(
        self,
        *,
        code: str,
        client_id: str,
        redirect_uri: str,
        code_verifier: str | None = None,
    ) -> TokenResponse:
        """Exchange an authorization code for tokens.

        Parameters
        ----------
        code : str
            The authorization code.
        client_id : str
            The client that obtained the code.
        redirect_uri : str
            Must match the redirect_uri used in the authorization request.
        code_verifier : str | None
            PKCE code verifier (required if code_challenge was used).

        Returns
        -------
        TokenResponse
            The token response.

        Raises
        ------
        TokenError
            If the code is invalid, expired, or parameters don't match.
        """
        # Look up the authorization code
        auth_code = await self._get_authorization_code(code)
        if auth_code is None:
            raise TokenError("invalid_grant", "Invalid authorization code")

        # Check not expired
        now = datetime.now(timezone.utc)
        expires_at = auth_code.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < now:
            raise TokenError("invalid_grant", "Authorization code expired")

        # Check not already used
        if auth_code.is_used:
            raise TokenError("invalid_grant", "Authorization code already used")

        # Check client matches
        if auth_code.client_id != client_id:
            raise TokenError("invalid_grant", "Client mismatch")

        # Check redirect_uri matches
        if auth_code.redirect_uri != redirect_uri:
            raise TokenError("invalid_grant", "Redirect URI mismatch")

        # PKCE verification
        if auth_code.code_challenge:
            if not code_verifier:
                raise TokenError("invalid_grant", "code_verifier required")
            if not self._verify_pkce(
                code_verifier,
                auth_code.code_challenge,
                auth_code.code_challenge_method or "S256",
            ):
                raise TokenError("invalid_grant", "PKCE verification failed")

        # Mark code as used
        auth_code.is_used = True
        auth_code.used_at = now
        await self.session.flush()

        # Generate tokens
        scopes = auth_code.scopes.split() if auth_code.scopes else []
        jti = uuid.uuid4().hex

        # Create access token record
        access_token_record = AccessToken(
            jti=jti,
            user_id=auth_code.user_id,
            client_id=client_id,
            scopes=auth_code.scopes,
            expires_at=now + timedelta(seconds=self.settings.jwt_access_token_exp),
        )
        self.session.add(access_token_record)

        # Create refresh token
        raw_refresh = uuid.uuid4().hex
        refresh_hash = hashlib.sha256(raw_refresh.encode()).hexdigest()
        family_id = uuid.uuid4()
        refresh_record = RefreshToken(
            token_hash=refresh_hash,
            family_id=family_id,
            user_id=auth_code.user_id,
            client_id=client_id,
            scopes=auth_code.scopes,
            expires_at=now + timedelta(days=30),
        )
        self.session.add(refresh_record)
        await self.session.flush()

        # Build JWT access token
        access_jwt = self._build_access_jwt(
            sub=str(auth_code.user_id),
            aud=client_id,
            jti=jti,
            scopes=scopes,
        )

        # Build ID token if openid scope
        id_token: str | None = None
        if "openid" in scopes:
            id_token = self._build_id_token(
                sub=str(auth_code.user_id),
                aud=client_id,
                nonce=auth_code.nonce,
            )

        return TokenResponse(
            access_token=access_jwt,
            expires_in=self.settings.jwt_access_token_exp,
            refresh_token=raw_refresh,
            scope=" ".join(scopes),
            id_token=id_token,
        )

    async def issue_client_credentials(
        self,
        *,
        client_id: str,
        client_scopes: list[str],
        requested_scope: str | None = None,
    ) -> TokenResponse:
        """Issue tokens for a client_credentials grant (RFC 6749 §4.4).

        Parameters
        ----------
        client_id : str
            The authenticated client identifier.
        client_scopes : list[str]
            Scopes the client is allowed to request.
        requested_scope : str or None
            Space-separated scopes requested by the client.
            If None, all allowed scopes are granted.

        Returns
        -------
        TokenResponse
            The token response (access_token only, no refresh_token or id_token).

        Raises
        ------
        TokenError
            If the requested scope is not allowed.
        """
        # Determine granted scopes
        if requested_scope:
            requested = requested_scope.split()
            invalid = [s for s in requested if s not in client_scopes]
            if invalid:
                raise TokenError(
                    "invalid_scope",
                    f"Scope not allowed: {' '.join(invalid)}",
                )
            granted_scopes = requested
        else:
            granted_scopes = list(client_scopes)

        # Generate access token
        now = datetime.now(timezone.utc)
        jti = uuid.uuid4().hex

        access_token_record = AccessToken(
            jti=jti,
            user_id=None,
            client_id=client_id,
            scopes=" ".join(granted_scopes),
            expires_at=now + timedelta(seconds=self.settings.jwt_access_token_exp),
        )
        self.session.add(access_token_record)
        await self.session.flush()

        access_jwt = self._build_access_jwt(
            sub=client_id,
            aud=client_id,
            jti=jti,
            scopes=granted_scopes,
        )

        return TokenResponse(
            access_token=access_jwt,
            expires_in=self.settings.jwt_access_token_exp,
            scope=" ".join(granted_scopes),
        )

    async def _get_authorization_code(self, code: str) -> AuthorizationCode | None:
        """Look up an authorization code.

        Parameters
        ----------
        code : str
            The code value.

        Returns
        -------
        AuthorizationCode or None
        """
        stmt = select(AuthorizationCode).where(AuthorizationCode.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def _build_access_jwt(
        self, *, sub: str, aud: str, jti: str, scopes: list[str]
    ) -> str:
        """Build a signed JWT access token (simplified — no JWK lookup).

        For now returns a simple opaque-style token. Full JWT signing
        via JWKService will be integrated when the JWK is seeded.
        """
        import jwt as pyjwt

        now = datetime.now(timezone.utc)
        payload = {
            "iss": self.settings.jwt_issuer,
            "sub": sub,
            "aud": aud,
            "exp": now + timedelta(seconds=self.settings.jwt_access_token_exp),
            "iat": now,
            "jti": jti,
            "scope": " ".join(scopes),
        }
        # Use HS256 with a secret as fallback (no RSA key required)
        return pyjwt.encode(
            payload, self.settings.jwk_encryption_key or "dev-secret", algorithm="HS256"
        )

    def _build_id_token(self, *, sub: str, aud: str, nonce: str | None) -> str:
        """Build a signed OIDC ID token (simplified)."""
        import jwt as pyjwt

        now = datetime.now(timezone.utc)
        payload: dict[str, Any] = {
            "iss": self.settings.jwt_issuer,
            "sub": sub,
            "aud": aud,
            "exp": now + timedelta(seconds=self.settings.jwt_id_token_exp),
            "iat": now,
        }
        if nonce:
            payload["nonce"] = nonce
        return pyjwt.encode(
            payload, self.settings.jwk_encryption_key or "dev-secret", algorithm="HS256"
        )

    @staticmethod
    def _verify_pkce(code_verifier: str, code_challenge: str, method: str) -> bool:
        """Verify PKCE code_verifier against code_challenge.

        Parameters
        ----------
        code_verifier : str
            The verifier from the token request.
        code_challenge : str
            The challenge from the authorization request.
        method : str
            ``S256`` or ``plain``.

        Returns
        -------
        bool
        """
        import base64

        if method == "plain":
            return code_verifier == code_challenge
        if method == "S256":
            digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
            computed = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
            return computed == code_challenge
        return False

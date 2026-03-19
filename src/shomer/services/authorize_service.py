# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""OAuth2 authorization request validation service per RFC 6749 §4.1."""

from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from shomer.models.authorization_code import AuthorizationCode
from shomer.services.oauth2_client_service import (
    InvalidRedirectURIError,
    OAuth2ClientService,
)

#: Default authorization code lifetime.
AUTH_CODE_TTL = timedelta(minutes=10)


class AuthorizeError(Exception):
    """Base error for authorization request failures.

    Attributes
    ----------
    error : str
        OAuth2 error code per RFC 6749 §4.1.2.1.
    description : str
        Human-readable error description.
    """

    def __init__(self, error: str, description: str) -> None:
        self.error = error
        self.description = description
        super().__init__(description)


@dataclass
class AuthorizeRequest:
    """Parsed and validated authorization request parameters.

    Attributes
    ----------
    client_id : str
        The OAuth2 client identifier.
    redirect_uri : str
        The validated redirect URI.
    response_type : str
        Requested response type (``code``).
    scope : str
        Space-separated requested scopes.
    state : str
        Opaque state parameter for CSRF protection.
    nonce : str or None
        OIDC nonce for ID token binding.
    prompt : str or None
        OIDC prompt parameter (login, consent, none).
    login_hint : str or None
        OIDC login hint.
    code_challenge : str or None
        PKCE code challenge.
    code_challenge_method : str or None
        PKCE challenge method (S256 or plain).
    validated_scopes : list[str]
        Scopes validated against client allowed scopes.
    """

    client_id: str
    redirect_uri: str
    response_type: str
    scope: str = ""
    state: str = ""
    nonce: str | None = None
    prompt: str | None = None
    login_hint: str | None = None
    code_challenge: str | None = None
    code_challenge_method: str | None = None
    validated_scopes: list[str] = field(default_factory=list)


class AuthorizeService:
    """Validate OAuth2 authorization requests and issue authorization codes.

    Attributes
    ----------
    session : AsyncSession
        Database session.
    client_service : OAuth2ClientService
        Client management service.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.client_service = OAuth2ClientService(session)

    async def validate_request(
        self,
        *,
        client_id: str | None,
        redirect_uri: str | None,
        response_type: str | None,
        scope: str | None,
        state: str | None,
        nonce: str | None = None,
        prompt: str | None = None,
        login_hint: str | None = None,
        code_challenge: str | None = None,
        code_challenge_method: str | None = None,
    ) -> AuthorizeRequest:
        """Validate all authorization request parameters.

        Parameters
        ----------
        client_id : str or None
            OAuth2 client identifier.
        redirect_uri : str or None
            Requested redirect URI.
        response_type : str or None
            Requested response type.
        scope : str or None
            Requested scopes.
        state : str or None
            CSRF state parameter.
        nonce : str or None
            OIDC nonce.
        prompt : str or None
            OIDC prompt.
        login_hint : str or None
            OIDC login hint.
        code_challenge : str or None
            PKCE code challenge.
        code_challenge_method : str or None
            PKCE challenge method.

        Returns
        -------
        AuthorizeRequest
            The validated request.

        Raises
        ------
        AuthorizeError
            If any parameter is invalid.
        """
        # client_id is required
        if not client_id:
            raise AuthorizeError("invalid_request", "client_id is required")

        # Look up client
        client = await self.client_service.get_by_client_id(client_id)
        if client is None:
            raise AuthorizeError("invalid_request", "Unknown client_id")

        # redirect_uri is required
        if not redirect_uri:
            raise AuthorizeError("invalid_request", "redirect_uri is required")

        # Validate redirect_uri against client
        try:
            self.client_service.validate_redirect_uri(client, redirect_uri)
        except InvalidRedirectURIError as exc:
            raise AuthorizeError("invalid_request", str(exc)) from exc

        # response_type is required and must be "code"
        if not response_type:
            raise AuthorizeError("invalid_request", "response_type is required")
        if response_type != "code":
            raise AuthorizeError(
                "unsupported_response_type",
                f"Unsupported response_type: {response_type}",
            )
        if "code" not in client.response_types:
            raise AuthorizeError(
                "unauthorized_client",
                "Client not authorized for response_type=code",
            )

        # Validate scopes
        requested_scopes = (scope or "").split()
        client_scopes = set(client.scopes)
        validated_scopes = [s for s in requested_scopes if s in client_scopes]

        # state is recommended (we require it for CSRF protection)
        if not state:
            raise AuthorizeError("invalid_request", "state is required")

        # PKCE validation (enforcement for public clients is in #38/#39)
        if code_challenge and code_challenge_method not in ("S256", "plain", None):
            raise AuthorizeError(
                "invalid_request",
                f"Unsupported code_challenge_method: {code_challenge_method}",
            )

        return AuthorizeRequest(
            client_id=client_id,
            redirect_uri=redirect_uri,
            response_type=response_type,
            scope=scope or "",
            state=state,
            nonce=nonce,
            prompt=prompt,
            login_hint=login_hint,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method
            or ("S256" if code_challenge else None),
            validated_scopes=validated_scopes,
        )

    async def create_authorization_code(
        self,
        *,
        request: AuthorizeRequest,
        user_id: uuid.UUID,
    ) -> str:
        """Issue an authorization code after user consent.

        Parameters
        ----------
        request : AuthorizeRequest
            The validated authorization request.
        user_id : uuid.UUID
            The authenticated user's ID.

        Returns
        -------
        str
            The authorization code value.
        """
        code = secrets.token_urlsafe(32)
        auth_code = AuthorizationCode(
            code=code,
            user_id=user_id,
            client_id=request.client_id,
            redirect_uri=request.redirect_uri,
            scopes=" ".join(request.validated_scopes),
            nonce=request.nonce,
            code_challenge=request.code_challenge,
            code_challenge_method=request.code_challenge_method,
            expires_at=datetime.now(timezone.utc) + AUTH_CODE_TTL,
        )
        self.session.add(auth_code)
        await self.session.flush()
        return code

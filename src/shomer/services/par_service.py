# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Pushed Authorization Request service per RFC 9126."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from shomer.models.par_request import PARRequest
from shomer.services.authorize_service import AuthorizeService

#: Default PAR request lifetime (60 seconds per RFC 9126 §2.2).
PAR_TTL = timedelta(seconds=60)


class PARError(Exception):
    """Raised when a Pushed Authorization Request fails.

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


@dataclass
class PARResponse:
    """Successful PAR response per RFC 9126 §2.2.

    Attributes
    ----------
    request_uri : str
        The ``urn:ietf:params:oauth:request_uri:...`` identifier.
    expires_in : int
        Lifetime of the request_uri in seconds.
    """

    request_uri: str
    expires_in: int


class PARService:
    """Handle Pushed Authorization Requests per RFC 9126.

    Validates authorization parameters (same rules as ``/authorize``),
    stores them in the database, and returns a ``request_uri`` the client
    can use at the authorization endpoint.

    Attributes
    ----------
    session : AsyncSession
        Database session.
    authorize_service : AuthorizeService
        Service for parameter validation.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.authorize_service = AuthorizeService(session)

    async def push_authorization_request(
        self,
        *,
        client_id: str,
        redirect_uri: str | None = None,
        response_type: str | None = None,
        scope: str | None = None,
        state: str | None = None,
        nonce: str | None = None,
        code_challenge: str | None = None,
        code_challenge_method: str | None = None,
    ) -> PARResponse:
        """Validate and store a pushed authorization request.

        Parameters
        ----------
        client_id : str
            The authenticated client identifier.
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
        code_challenge : str or None
            PKCE code challenge.
        code_challenge_method : str or None
            PKCE challenge method.

        Returns
        -------
        PARResponse
            The request_uri and expiration.

        Raises
        ------
        PARError
            If parameter validation fails.
        """
        from shomer.services.authorize_service import AuthorizeError

        try:
            await self.authorize_service.validate_request(
                client_id=client_id,
                redirect_uri=redirect_uri,
                response_type=response_type,
                scope=scope,
                state=state,
                nonce=nonce,
                code_challenge=code_challenge,
                code_challenge_method=code_challenge_method,
            )
        except AuthorizeError as exc:
            raise PARError(exc.error, exc.description) from exc

        # Generate request_uri per RFC 9126 §2.2
        token = secrets.token_urlsafe(32)
        request_uri = f"urn:ietf:params:oauth:request_uri:{token}"

        now = datetime.now(timezone.utc)
        expires_at = now + PAR_TTL

        # Store all parameters as JSON
        parameters: dict[str, str | None] = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": response_type,
            "scope": scope,
            "state": state,
            "nonce": nonce,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
        }

        par_request = PARRequest(
            request_uri=request_uri,
            client_id=client_id,
            parameters=parameters,
            expires_at=expires_at,
        )
        self.session.add(par_request)
        await self.session.flush()

        return PARResponse(
            request_uri=request_uri,
            expires_in=int(PAR_TTL.total_seconds()),
        )

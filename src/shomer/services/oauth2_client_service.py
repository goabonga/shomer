# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""OAuth2 client management service per RFC 6749 §2.3."""

from __future__ import annotations

import base64
import secrets
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shomer.core.security import hash_password, verify_password
from shomer.models.oauth2_client import (
    ClientType,
    OAuth2Client,
    TokenEndpointAuthMethod,
)


class InvalidClientError(Exception):
    """Raised when client authentication fails."""


class InvalidRedirectURIError(Exception):
    """Raised when a redirect URI is invalid."""


class OAuth2ClientService:
    """Manage OAuth2 clients: creation, authentication, redirect validation.

    Attributes
    ----------
    session : AsyncSession
        Database session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_client(
        self,
        *,
        client_name: str,
        client_type: ClientType = ClientType.CONFIDENTIAL,
        redirect_uris: list[str] | None = None,
        grant_types: list[str] | None = None,
        response_types: list[str] | None = None,
        scopes: list[str] | None = None,
        token_endpoint_auth_method: TokenEndpointAuthMethod | None = None,
    ) -> tuple[OAuth2Client, str | None]:
        """Create a new OAuth2 client.

        Generates a random ``client_id`` and, for confidential clients,
        a random ``client_secret`` hashed with Argon2id.

        Parameters
        ----------
        client_name : str
            Human-readable client name.
        client_type : ClientType
            Confidential or public.
        redirect_uris : list[str] or None
            Allowed redirect URIs.
        grant_types : list[str] or None
            Allowed grant types.
        response_types : list[str] or None
            Allowed response types.
        scopes : list[str] or None
            Allowed scopes.
        token_endpoint_auth_method : TokenEndpointAuthMethod or None
            Auth method. Defaults to ``client_secret_basic`` for
            confidential, ``none`` for public.

        Returns
        -------
        tuple[OAuth2Client, str | None]
            The created client and the raw client_secret (None for public).
        """
        client_id = secrets.token_urlsafe(24)
        raw_secret: str | None = None
        secret_hash: str | None = None

        if client_type == ClientType.CONFIDENTIAL:
            raw_secret = secrets.token_urlsafe(48)
            secret_hash = hash_password(raw_secret)

        if token_endpoint_auth_method is None:
            token_endpoint_auth_method = (
                TokenEndpointAuthMethod.CLIENT_SECRET_BASIC
                if client_type == ClientType.CONFIDENTIAL
                else TokenEndpointAuthMethod.NONE
            )

        # Validate redirect URIs
        for uri in redirect_uris or []:
            self._validate_redirect_uri(uri)

        client = OAuth2Client(
            client_id=client_id,
            client_secret_hash=secret_hash,
            client_name=client_name,
            client_type=client_type,
            redirect_uris=redirect_uris or [],
            grant_types=grant_types or [],
            response_types=response_types or [],
            scopes=scopes or [],
            token_endpoint_auth_method=token_endpoint_auth_method,
        )
        self.session.add(client)
        await self.session.flush()
        return client, raw_secret

    async def get_by_client_id(self, client_id: str) -> OAuth2Client | None:
        """Look up a client by its client_id.

        Parameters
        ----------
        client_id : str
            The unique client identifier.

        Returns
        -------
        OAuth2Client or None
            The client if found and active.
        """
        stmt = select(OAuth2Client).where(
            OAuth2Client.client_id == client_id,
            OAuth2Client.is_active == True,  # noqa: E712
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def authenticate_client(
        self,
        *,
        authorization_header: str | None = None,
        body_client_id: str | None = None,
        body_client_secret: str | None = None,
    ) -> OAuth2Client:
        """Authenticate an OAuth2 client per RFC 6749 §2.3.

        Supports ``client_secret_basic`` (HTTP Basic), ``client_secret_post``
        (POST body), and ``none`` (public client).

        Parameters
        ----------
        authorization_header : str or None
            Value of the ``Authorization`` header (for Basic auth).
        body_client_id : str or None
            ``client_id`` from the request body.
        body_client_secret : str or None
            ``client_secret`` from the request body.

        Returns
        -------
        OAuth2Client
            The authenticated client.

        Raises
        ------
        InvalidClientError
            If authentication fails.
        """
        client_id: str | None = None
        client_secret: str | None = None

        # Try HTTP Basic first (RFC 6749 §2.3.1)
        if authorization_header and authorization_header.startswith("Basic "):
            client_id, client_secret = self._parse_basic_auth(authorization_header)
        elif body_client_id:
            client_id = body_client_id
            client_secret = body_client_secret

        if not client_id:
            raise InvalidClientError("Missing client credentials")

        client = await self.get_by_client_id(client_id)
        if client is None:
            # Dummy hash to prevent timing enumeration
            hash_password("dummy")
            raise InvalidClientError("Invalid client credentials")

        method = client.token_endpoint_auth_method

        if method == TokenEndpointAuthMethod.NONE:
            # Public client — no secret required
            if client.client_type != ClientType.PUBLIC:
                raise InvalidClientError(
                    "auth method 'none' only allowed for public clients"
                )
            return client

        if method in (
            TokenEndpointAuthMethod.CLIENT_SECRET_BASIC,
            TokenEndpointAuthMethod.CLIENT_SECRET_POST,
        ):
            if not client_secret or not client.client_secret_hash:
                raise InvalidClientError("Client secret required")
            if not verify_password(client_secret, client.client_secret_hash):
                raise InvalidClientError("Invalid client credentials")
            return client

        raise InvalidClientError(f"Unsupported auth method: {method}")

    async def rotate_secret(self, client_id: str) -> tuple[OAuth2Client, str]:
        """Generate a new secret for a confidential client.

        Parameters
        ----------
        client_id : str
            The client identifier.

        Returns
        -------
        tuple[OAuth2Client, str]
            The updated client and the new raw secret.

        Raises
        ------
        InvalidClientError
            If the client is not found or is public.
        """
        client = await self.get_by_client_id(client_id)
        if client is None:
            raise InvalidClientError("Client not found")
        if client.client_type == ClientType.PUBLIC:
            raise InvalidClientError("Cannot rotate secret for public client")

        new_secret = secrets.token_urlsafe(48)
        client.client_secret_hash = hash_password(new_secret)
        await self.session.flush()
        return client, new_secret

    def validate_redirect_uri(self, client: OAuth2Client, redirect_uri: str) -> None:
        """Validate a redirect URI against the client's registered URIs.

        Per RFC 6749 §3.1.2.2: exact string match, no fragments.

        Parameters
        ----------
        client : OAuth2Client
            The client to validate against.
        redirect_uri : str
            The URI to validate.

        Raises
        ------
        InvalidRedirectURIError
            If the URI is not registered or contains a fragment.
        """
        self._validate_redirect_uri(redirect_uri)
        if redirect_uri not in client.redirect_uris:
            raise InvalidRedirectURIError(
                f"Redirect URI not registered: {redirect_uri}"
            )

    @staticmethod
    def _validate_redirect_uri(uri: str) -> None:
        """Validate a redirect URI format.

        Parameters
        ----------
        uri : str
            URI to validate.

        Raises
        ------
        InvalidRedirectURIError
            If the URI has a fragment or is malformed.
        """
        parsed = urlparse(uri)
        if parsed.fragment:
            raise InvalidRedirectURIError("Redirect URI must not contain a fragment")
        if not parsed.scheme or not parsed.netloc:
            raise InvalidRedirectURIError(f"Malformed redirect URI: {uri}")

    @staticmethod
    def _parse_basic_auth(header: str) -> tuple[str, str]:
        """Parse an HTTP Basic Authorization header.

        Parameters
        ----------
        header : str
            The full ``Authorization: Basic ...`` header value.

        Returns
        -------
        tuple[str, str]
            ``(client_id, client_secret)``.

        Raises
        ------
        InvalidClientError
            If the header is malformed.
        """
        try:
            encoded = header[len("Basic ") :]
            decoded = base64.b64decode(encoded).decode("utf-8")
            client_id, client_secret = decoded.split(":", 1)
            return client_id, client_secret
        except Exception as exc:
            raise InvalidClientError("Malformed Basic Authorization header") from exc

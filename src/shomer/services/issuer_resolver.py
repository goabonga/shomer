# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Dynamic issuer resolver for multi-tenant OAuth2/OIDC."""

from __future__ import annotations

import uuid

from shomer.core.settings import Settings


class IssuerResolver:
    """Resolve the issuer URL based on the current tenant context.

    In a multi-tenant setup, each tenant may have its own issuer URL
    (e.g. ``https://tenant1.auth.example.com``). This service provides
    the correct issuer for JWT ``iss`` claims, OIDC discovery, and
    token responses.

    Attributes
    ----------
    settings : Settings
        Application configuration with the default issuer.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def resolve(self, tenant_id: uuid.UUID | None = None) -> str:
        """Resolve the issuer URL for the given tenant.

        Parameters
        ----------
        tenant_id : uuid.UUID or None
            The current tenant ID. ``None`` means no tenant context
            (single-tenant mode).

        Returns
        -------
        str
            The issuer URL. Falls back to the default ``jwt_issuer``
            setting when no tenant-specific issuer is configured.
        """
        if tenant_id is not None:
            tenant_issuer = self._lookup_tenant_issuer(tenant_id)
            if tenant_issuer is not None:
                return tenant_issuer

        return self.settings.jwt_issuer

    def get_token_endpoint(self, tenant_id: uuid.UUID | None = None) -> str:
        """Return the token endpoint URL for the given tenant.

        Parameters
        ----------
        tenant_id : uuid.UUID or None
            The current tenant ID.

        Returns
        -------
        str
            The token endpoint URL.
        """
        return f"{self.resolve(tenant_id)}/auth/token"

    def get_authorization_endpoint(self, tenant_id: uuid.UUID | None = None) -> str:
        """Return the authorization endpoint URL for the given tenant.

        Parameters
        ----------
        tenant_id : uuid.UUID or None
            The current tenant ID.

        Returns
        -------
        str
            The authorization endpoint URL.
        """
        return f"{self.resolve(tenant_id)}/auth/authorize"

    def get_jwks_uri(self, tenant_id: uuid.UUID | None = None) -> str:
        """Return the JWKS URI for the given tenant.

        Parameters
        ----------
        tenant_id : uuid.UUID or None
            The current tenant ID.

        Returns
        -------
        str
            The JWKS endpoint URL.
        """
        return f"{self.resolve(tenant_id)}/.well-known/jwks.json"

    def get_userinfo_endpoint(self, tenant_id: uuid.UUID | None = None) -> str:
        """Return the userinfo endpoint URL for the given tenant.

        Parameters
        ----------
        tenant_id : uuid.UUID or None
            The current tenant ID.

        Returns
        -------
        str
            The userinfo endpoint URL.
        """
        return f"{self.resolve(tenant_id)}/userinfo"

    @staticmethod
    def _lookup_tenant_issuer(tenant_id: uuid.UUID) -> str | None:
        """Look up a tenant-specific issuer URL.

        This is a placeholder. The real implementation will query the
        tenant table (M18) to resolve custom domains and issuers.

        Parameters
        ----------
        tenant_id : uuid.UUID
            Tenant to look up.

        Returns
        -------
        str or None
            The tenant issuer URL, or ``None`` if not configured.
        """
        # Placeholder — will be wired in M18 (multi-tenancy)
        return None

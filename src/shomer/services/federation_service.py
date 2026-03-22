# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Federation service for external identity providers.

Handles IdP listing, OIDC discovery, authorization URL generation,
token exchange, user info extraction, and JIT user provisioning.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shomer.models.federated_identity import FederatedIdentity
from shomer.models.identity_provider import IdentityProvider, IdentityProviderType
from shomer.models.tenant import Tenant
from shomer.models.tenant_member import TenantMember

logger = logging.getLogger(__name__)


@dataclass
class OIDCDiscoveryDocument:
    """Parsed OIDC discovery document.

    Attributes
    ----------
    issuer : str
        Token issuer URL.
    authorization_endpoint : str
        Authorization URL.
    token_endpoint : str
        Token URL.
    userinfo_endpoint : str or None
        Userinfo URL.
    jwks_uri : str
        JWKS endpoint.
    scopes_supported : list[str] or None
        Supported scopes.
    response_types_supported : list[str] or None
        Supported response types.
    claims_supported : list[str] or None
        Supported claims.
    """

    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str | None = None
    jwks_uri: str = ""
    scopes_supported: list[str] | None = None
    response_types_supported: list[str] | None = None
    claims_supported: list[str] | None = None


@dataclass
class FederationState:
    """State preserved through the federation flow.

    Attributes
    ----------
    tenant_slug : str
        Tenant slug.
    idp_id : str
        Identity provider ID.
    nonce : str
        OIDC nonce.
    code_verifier : str or None
        PKCE code verifier.
    original_state : str or None
        Original OAuth2 state from client.
    redirect_uri : str or None
        Where to redirect after federation.
    internal_state : str
        Internal state for CSRF.
    """

    tenant_slug: str
    idp_id: str
    nonce: str
    code_verifier: str | None = None
    original_state: str | None = None
    redirect_uri: str | None = None
    internal_state: str = ""


@dataclass
class FederatedUserInfo:
    """User information extracted from IdP response.

    Attributes
    ----------
    subject : str
        IdP's unique user identifier.
    email : str or None
        User email.
    email_verified : bool
        Whether email is verified by the IdP.
    name : str or None
        Full name.
    given_name : str or None
        First name.
    family_name : str or None
        Last name.
    picture : str or None
        Profile picture URL.
    username : str or None
        Username / preferred_username.
    raw_claims : dict[str, Any]
        Full raw claims from IdP.
    """

    subject: str
    email: str | None = None
    email_verified: bool = False
    name: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    picture: str | None = None
    username: str | None = None
    raw_claims: dict[str, Any] = field(default_factory=dict)


class FederationService:
    """Handle federated identity provider authentication.

    Attributes
    ----------
    session : AsyncSession
        Database session.
    """

    #: Well-known endpoints for social providers.
    PROVIDER_CONFIGS: dict[IdentityProviderType, dict[str, str]] = {
        IdentityProviderType.GOOGLE: {
            "discovery_url": "https://accounts.google.com/.well-known/openid-configuration",
            "scopes": "openid profile email",
        },
        IdentityProviderType.GITHUB: {
            "authorization_endpoint": "https://github.com/login/oauth/authorize",
            "token_endpoint": "https://github.com/login/oauth/access_token",
            "userinfo_endpoint": "https://api.github.com/user",
            "scopes": "read:user user:email",
        },
        IdentityProviderType.MICROSOFT: {
            "discovery_url": (
                "https://login.microsoftonline.com/common/v2.0"
                "/.well-known/openid-configuration"
            ),
            "scopes": "openid profile email",
        },
    }

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── IdP listing ───────────────────────────────────────────────────

    async def get_tenant_identity_providers(
        self, tenant_slug: str
    ) -> list[IdentityProvider]:
        """Get all active identity providers for a tenant.

        Parameters
        ----------
        tenant_slug : str
            Tenant slug.

        Returns
        -------
        list[IdentityProvider]
            Active IdPs ordered by display_order.
        """
        stmt = (
            select(IdentityProvider)
            .join(Tenant)
            .where(
                Tenant.slug == tenant_slug,
                Tenant.is_active == True,  # noqa: E712
                IdentityProvider.is_active == True,  # noqa: E712
            )
            .order_by(IdentityProvider.display_order, IdentityProvider.name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_identity_provider(self, idp_id: str) -> IdentityProvider | None:
        """Get an identity provider by ID.

        Parameters
        ----------
        idp_id : str
            Identity provider ID.

        Returns
        -------
        IdentityProvider or None
            The IdP if found.
        """
        stmt = select(IdentityProvider).where(IdentityProvider.id == idp_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ── OIDC discovery ────────────────────────────────────────────────

    async def fetch_oidc_discovery(self, discovery_url: str) -> OIDCDiscoveryDocument:
        """Fetch and parse an OIDC discovery document.

        Parameters
        ----------
        discovery_url : str
            URL to ``.well-known/openid-configuration``.

        Returns
        -------
        OIDCDiscoveryDocument
            The parsed discovery document.

        Raises
        ------
        Exception
            If the request fails or the document is invalid.
        """
        import httpx

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(discovery_url)
            response.raise_for_status()
            data = response.json()

        return OIDCDiscoveryDocument(
            issuer=data["issuer"],
            authorization_endpoint=data["authorization_endpoint"],
            token_endpoint=data["token_endpoint"],
            userinfo_endpoint=data.get("userinfo_endpoint"),
            jwks_uri=data.get("jwks_uri", ""),
            scopes_supported=data.get("scopes_supported"),
            response_types_supported=data.get("response_types_supported"),
            claims_supported=data.get("claims_supported"),
        )

    # ── Authorization URL ─────────────────────────────────────────────

    async def get_authorization_url(
        self,
        idp: IdentityProvider,
        callback_url: str,
        state: str,
        nonce: str,
        code_verifier: str | None = None,
    ) -> str:
        """Generate the authorization URL for an IdP.

        Parameters
        ----------
        idp : IdentityProvider
            IdP configuration.
        callback_url : str
            Callback URL for the redirect.
        state : str
            State parameter for CSRF protection.
        nonce : str
            Nonce for ID token validation.
        code_verifier : str or None
            Optional PKCE code verifier.

        Returns
        -------
        str
            Authorization URL to redirect the user to.
        """
        auth_endpoint = await self._get_authorization_endpoint(idp)
        scopes = idp.scopes or ["openid", "profile", "email"]

        params: dict[str, str] = {
            "client_id": idp.client_id,
            "redirect_uri": callback_url,
            "response_type": "code",
            "scope": " ".join(scopes),
            "state": state,
        }

        if idp.provider_type != IdentityProviderType.GITHUB:
            params["nonce"] = nonce

        if code_verifier:
            params["code_challenge"] = self._generate_code_challenge(code_verifier)
            params["code_challenge_method"] = "S256"

        return f"{auth_endpoint}?{urlencode(params)}"

    # ── Token exchange ────────────────────────────────────────────────

    async def exchange_code_for_tokens(
        self,
        idp: IdentityProvider,
        code: str,
        callback_url: str,
        code_verifier: str | None = None,
    ) -> dict[str, Any]:
        """Exchange authorization code for tokens.

        Parameters
        ----------
        idp : IdentityProvider
            IdP configuration.
        code : str
            Authorization code from IdP.
        callback_url : str
            Callback URL used in authorization request.
        code_verifier : str or None
            PKCE code verifier.

        Returns
        -------
        dict[str, Any]
            Token response from IdP.
        """
        import httpx

        token_endpoint = await self._get_token_endpoint(idp)

        data: dict[str, str] = {
            "grant_type": "authorization_code",
            "client_id": idp.client_id,
            "code": code,
            "redirect_uri": callback_url,
        }

        if idp.client_secret_encrypted:
            from shomer.core.security import AESEncryption
            from shomer.core.settings import get_settings

            settings = get_settings()
            key = settings.jwk_encryption_key
            if key:
                enc = AESEncryption.from_base64(key)
                data["client_secret"] = enc.decrypt(idp.client_secret_encrypted).decode(
                    "utf-8"
                )

        if code_verifier:
            data["code_verifier"] = code_verifier

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                token_endpoint,
                data=data,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result

    # ── User info ─────────────────────────────────────────────────────

    async def get_user_info(
        self,
        idp: IdentityProvider,
        access_token: str,
        id_token: str | None = None,
    ) -> FederatedUserInfo:
        """Get user information from IdP.

        Parameters
        ----------
        idp : IdentityProvider
            IdP configuration.
        access_token : str
            Access token from IdP.
        id_token : str or None
            Optional ID token.

        Returns
        -------
        FederatedUserInfo
            Extracted user information.
        """
        import httpx
        import jwt as pyjwt

        claims: dict[str, Any] = {}
        if id_token:
            claims = pyjwt.decode(
                id_token,
                options={"verify_signature": False},
                algorithms=["RS256", "HS256", "ES256"],
            )

        userinfo_endpoint = await self._get_userinfo_endpoint(idp)
        if userinfo_endpoint:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    userinfo_endpoint,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                if response.status_code == 200:
                    claims.update(response.json())

        if idp.provider_type == IdentityProviderType.GITHUB:
            return await self._get_github_user_info(access_token, claims)

        claims = self._apply_attribute_mapping(claims, idp.attribute_mapping)

        return FederatedUserInfo(
            subject=str(claims.get("sub", "")),
            email=claims.get("email"),
            email_verified=claims.get("email_verified", False),
            name=claims.get("name"),
            given_name=claims.get("given_name"),
            family_name=claims.get("family_name"),
            picture=claims.get("picture"),
            username=claims.get("preferred_username"),
            raw_claims=claims,
        )

    # ── JIT provisioning ──────────────────────────────────────────────

    async def find_or_create_user(
        self,
        idp: IdentityProvider,
        user_info: FederatedUserInfo,
        tenant_slug: str,
    ) -> tuple[Any, FederatedIdentity, bool]:
        """Find existing user or create via JIT provisioning.

        Parameters
        ----------
        idp : IdentityProvider
            The identity provider.
        user_info : FederatedUserInfo
            User information from IdP.
        tenant_slug : str
            Tenant slug for membership.

        Returns
        -------
        tuple[User, FederatedIdentity, bool]
            (user, federated_identity, is_new_user).

        Raises
        ------
        ValueError
            If auto_provision is disabled and user not found.
        """
        from shomer.models.user import User
        from shomer.models.user_email import UserEmail
        from shomer.models.user_profile import UserProfile

        now = datetime.now(timezone.utc)

        # 1. Check existing federated identity
        stmt = select(FederatedIdentity).where(
            FederatedIdentity.identity_provider_id == idp.id,
            FederatedIdentity.external_subject == user_info.subject,
        )
        result = await self.session.execute(stmt)
        fed_id = result.scalar_one_or_none()

        if fed_id:
            fed_id.last_login_at = now
            fed_id.raw_claims = user_info.raw_claims
            user_result = await self.session.execute(
                select(User).where(User.id == fed_id.user_id)
            )
            existing_user = user_result.scalar_one()
            await self.session.flush()
            return existing_user, fed_id, False

        # 2. Check auto_provision
        if not idp.auto_provision:
            raise ValueError(
                "Auto-provisioning is disabled. Contact your administrator."
            )

        # 3. Try account linking by email
        user: Any = None
        if user_info.email and idp.allow_linking:
            link_result = await self.session.execute(
                select(User)
                .join(UserEmail)
                .where(UserEmail.email == user_info.email.lower())
            )
            user = link_result.scalar_one_or_none()

        # 4. Create new user if needed
        is_new = False
        if not user:
            user = User(is_active=True)
            self.session.add(user)
            await self.session.flush()
            is_new = True

            if user_info.email:
                self.session.add(
                    UserEmail(
                        user_id=user.id,
                        email=user_info.email.lower(),
                        is_primary=True,
                        is_verified=user_info.email_verified,
                    )
                )

            self.session.add(
                UserProfile(
                    user_id=user.id,
                    name=user_info.name,
                    given_name=user_info.given_name,
                    family_name=user_info.family_name,
                    picture_url=user_info.picture,
                    preferred_username=user_info.username,
                )
            )

        # 5. Create federated identity link
        fed_id = FederatedIdentity(
            user_id=user.id,
            identity_provider_id=idp.id,
            external_subject=user_info.subject,
            external_email=user_info.email,
            external_username=user_info.username,
            raw_claims=user_info.raw_claims,
            linked_at=now,
            last_login_at=now,
        )
        self.session.add(fed_id)

        # 6. Add to tenant
        tenant_result = await self.session.execute(
            select(Tenant).where(Tenant.slug == tenant_slug)
        )
        tenant = tenant_result.scalar_one_or_none()
        if tenant:
            member_result = await self.session.execute(
                select(TenantMember).where(
                    TenantMember.tenant_id == tenant.id,
                    TenantMember.user_id == user.id,
                )
            )
            if member_result.scalar_one_or_none() is None:
                self.session.add(
                    TenantMember(
                        tenant_id=tenant.id,
                        user_id=user.id,
                        role="member",
                        joined_at=now,
                    )
                )

        await self.session.flush()
        return user, fed_id, is_new

    # ── Internal helpers ──────────────────────────────────────────────

    async def _get_authorization_endpoint(self, idp: IdentityProvider) -> str:
        """Resolve authorization endpoint for an IdP."""
        if idp.authorization_endpoint:
            return idp.authorization_endpoint
        if idp.discovery_url:
            doc = await self.fetch_oidc_discovery(idp.discovery_url)
            return doc.authorization_endpoint
        config = self.PROVIDER_CONFIGS.get(idp.provider_type, {})
        if "discovery_url" in config:
            doc = await self.fetch_oidc_discovery(config["discovery_url"])
            return doc.authorization_endpoint
        if "authorization_endpoint" in config:
            return config["authorization_endpoint"]
        raise ValueError(f"Cannot resolve authorization endpoint for: {idp.name}")

    async def _get_token_endpoint(self, idp: IdentityProvider) -> str:
        """Resolve token endpoint for an IdP."""
        if idp.token_endpoint:
            return idp.token_endpoint
        if idp.discovery_url:
            doc = await self.fetch_oidc_discovery(idp.discovery_url)
            return doc.token_endpoint
        config = self.PROVIDER_CONFIGS.get(idp.provider_type, {})
        if "discovery_url" in config:
            doc = await self.fetch_oidc_discovery(config["discovery_url"])
            return doc.token_endpoint
        if "token_endpoint" in config:
            return config["token_endpoint"]
        raise ValueError(f"Cannot resolve token endpoint for: {idp.name}")

    async def _get_userinfo_endpoint(self, idp: IdentityProvider) -> str | None:
        """Resolve userinfo endpoint for an IdP."""
        if idp.userinfo_endpoint:
            return idp.userinfo_endpoint
        if idp.discovery_url:
            doc = await self.fetch_oidc_discovery(idp.discovery_url)
            return doc.userinfo_endpoint
        config = self.PROVIDER_CONFIGS.get(idp.provider_type, {})
        if "discovery_url" in config:
            doc = await self.fetch_oidc_discovery(config["discovery_url"])
            return doc.userinfo_endpoint
        return config.get("userinfo_endpoint")

    async def _get_github_user_info(
        self, access_token: str, _claims: dict[str, Any]
    ) -> FederatedUserInfo:
        """Get user info from GitHub API (non-OIDC)."""
        import httpx

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            response.raise_for_status()
            user_data = response.json()

            email_response = await client.get(
                "https://api.github.com/user/emails",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            emails = email_response.json() if email_response.status_code == 200 else []

        primary_email = None
        email_verified = False
        for e in emails:
            if e.get("primary"):
                primary_email = e.get("email")
                email_verified = e.get("verified", False)
                break

        name = user_data.get("name", "") or ""
        parts = name.split(" ", 1) if name else []

        return FederatedUserInfo(
            subject=str(user_data.get("id")),
            email=primary_email,
            email_verified=email_verified,
            name=name or None,
            given_name=parts[0] if parts else None,
            family_name=parts[1] if len(parts) > 1 else None,
            picture=user_data.get("avatar_url"),
            username=user_data.get("login"),
            raw_claims=user_data,
        )

    @staticmethod
    def _apply_attribute_mapping(
        claims: dict[str, Any], mapping: dict[str, str] | None
    ) -> dict[str, Any]:
        """Apply attribute mapping to transform IdP claims.

        Parameters
        ----------
        claims : dict
            Raw claims from IdP.
        mapping : dict or None
            Mapping from IdP claim → standard claim name.

        Returns
        -------
        dict
            Transformed claims.
        """
        if not mapping:
            return claims
        result = dict(claims)
        for idp_claim, standard_claim in mapping.items():
            if idp_claim in claims and standard_claim not in result:
                result[standard_claim] = claims[idp_claim]
        return result

    @staticmethod
    def _generate_code_challenge(code_verifier: str) -> str:
        """Generate S256 PKCE code challenge."""
        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

    @staticmethod
    def generate_state() -> str:
        """Generate a secure random state parameter."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_nonce() -> str:
        """Generate a secure random nonce."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_code_verifier() -> str:
        """Generate a PKCE code verifier."""
        return secrets.token_urlsafe(64)

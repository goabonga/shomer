# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for FederationService."""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

from shomer.models.identity_provider import IdentityProviderType
from shomer.services.federation_service import (
    FederatedUserInfo,
    FederationService,
    FederationState,
    OIDCDiscoveryDocument,
)


class TestProviderListing:
    """Tests for IdP listing."""

    def test_get_tenant_identity_providers(self) -> None:
        async def _run() -> None:
            idp = MagicMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [idp]
            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = FederationService(db)
            result = await svc.get_tenant_identity_providers("acme")
            assert len(result) == 1

        asyncio.run(_run())

    def test_get_identity_provider(self) -> None:
        async def _run() -> None:
            idp = MagicMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = idp
            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = FederationService(db)
            result = await svc.get_identity_provider(str(uuid.uuid4()))
            assert result is idp

        asyncio.run(_run())

    def test_get_identity_provider_not_found(self) -> None:
        async def _run() -> None:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = FederationService(db)
            result = await svc.get_identity_provider("unknown")
            assert result is None

        asyncio.run(_run())


class TestAuthorizationURL:
    """Tests for authorization URL generation."""

    def test_build_url_with_pkce(self) -> None:
        async def _run() -> None:
            idp = MagicMock()
            idp.provider_type = IdentityProviderType.OIDC
            idp.client_id = "my-client"
            idp.scopes = ["openid", "profile"]
            idp.authorization_endpoint = "https://idp.example.com/authorize"

            db = AsyncMock()
            svc = FederationService(db)
            url = await svc.get_authorization_url(
                idp=idp,
                callback_url="https://shomer.io/federation/callback",
                state="state123",
                nonce="nonce123",
                code_verifier="verifier123",
            )
            assert "client_id=my-client" in url
            assert "code_challenge=" in url
            assert "code_challenge_method=S256" in url
            assert "nonce=nonce123" in url
            assert "state=state123" in url

        asyncio.run(_run())

    def test_github_skips_nonce(self) -> None:
        async def _run() -> None:
            idp = MagicMock()
            idp.provider_type = IdentityProviderType.GITHUB
            idp.client_id = "gh-client"
            idp.scopes = ["read:user"]
            idp.authorization_endpoint = "https://github.com/login/oauth/authorize"

            db = AsyncMock()
            svc = FederationService(db)
            url = await svc.get_authorization_url(
                idp=idp,
                callback_url="https://shomer.io/cb",
                state="s",
                nonce="n",
            )
            assert "nonce=" not in url

        asyncio.run(_run())

    def test_default_scopes(self) -> None:
        async def _run() -> None:
            idp = MagicMock()
            idp.provider_type = IdentityProviderType.OIDC
            idp.client_id = "c"
            idp.scopes = None
            idp.authorization_endpoint = "https://idp.example.com/authorize"

            db = AsyncMock()
            svc = FederationService(db)
            url = await svc.get_authorization_url(
                idp=idp, callback_url="https://cb", state="s", nonce="n"
            )
            assert "openid" in url
            assert "profile" in url
            assert "email" in url

        asyncio.run(_run())


class TestSecurityHelpers:
    """Tests for state, nonce, code_verifier generation."""

    def test_generate_state(self) -> None:
        s = FederationService.generate_state()
        assert len(s) > 20

    def test_generate_nonce(self) -> None:
        n = FederationService.generate_nonce()
        assert len(n) > 20

    def test_generate_code_verifier(self) -> None:
        v = FederationService.generate_code_verifier()
        assert len(v) > 40

    def test_unique_values(self) -> None:
        s1 = FederationService.generate_state()
        s2 = FederationService.generate_state()
        assert s1 != s2

    def test_code_challenge(self) -> None:
        challenge = FederationService._generate_code_challenge("test-verifier")
        assert len(challenge) > 20
        assert "=" not in challenge  # No padding


class TestAttributeMapping:
    """Tests for _apply_attribute_mapping."""

    def test_no_mapping(self) -> None:
        claims = {"sub": "123", "email": "a@b.com"}
        result = FederationService._apply_attribute_mapping(claims, None)
        assert result == claims

    def test_mapping_applied(self) -> None:
        claims = {"mail": "a@b.com", "displayName": "John"}
        mapping = {"mail": "email", "displayName": "name"}
        result = FederationService._apply_attribute_mapping(claims, mapping)
        assert result["email"] == "a@b.com"
        assert result["name"] == "John"

    def test_no_overwrite_existing(self) -> None:
        claims = {"email": "original@b.com", "mail": "mapped@b.com"}
        mapping = {"mail": "email"}
        result = FederationService._apply_attribute_mapping(claims, mapping)
        assert result["email"] == "original@b.com"  # Not overwritten


class TestProviderConfigs:
    """Tests for PROVIDER_CONFIGS."""

    def test_google_config(self) -> None:
        config = FederationService.PROVIDER_CONFIGS[IdentityProviderType.GOOGLE]
        assert "discovery_url" in config
        assert "accounts.google.com" in config["discovery_url"]

    def test_github_config(self) -> None:
        config = FederationService.PROVIDER_CONFIGS[IdentityProviderType.GITHUB]
        assert "authorization_endpoint" in config
        assert "token_endpoint" in config

    def test_microsoft_config(self) -> None:
        config = FederationService.PROVIDER_CONFIGS[IdentityProviderType.MICROSOFT]
        assert "discovery_url" in config


class TestDataClasses:
    """Tests for dataclass construction."""

    def test_oidc_discovery_document(self) -> None:
        doc = OIDCDiscoveryDocument(
            issuer="https://idp.example.com",
            authorization_endpoint="https://idp.example.com/authorize",
            token_endpoint="https://idp.example.com/token",
        )
        assert doc.issuer == "https://idp.example.com"
        assert doc.userinfo_endpoint is None

    def test_federation_state(self) -> None:
        state = FederationState(tenant_slug="acme", idp_id="123", nonce="n")
        assert state.tenant_slug == "acme"
        assert state.code_verifier is None

    def test_federated_user_info(self) -> None:
        info = FederatedUserInfo(
            subject="sub-123",
            email="user@acme.com",
            email_verified=True,
            name="John Doe",
        )
        assert info.subject == "sub-123"
        assert info.email_verified is True
        assert info.raw_claims == {}

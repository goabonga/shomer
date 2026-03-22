# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for IdentityProvider model."""

import uuid

from shomer.models.identity_provider import IdentityProvider, IdentityProviderType


class TestIdentityProviderType:
    """Tests for IdentityProviderType enum."""

    def test_all_types(self) -> None:
        assert IdentityProviderType.OIDC.value == "oidc"
        assert IdentityProviderType.SAML.value == "saml"
        assert IdentityProviderType.GOOGLE.value == "google"
        assert IdentityProviderType.GITHUB.value == "github"
        assert IdentityProviderType.MICROSOFT.value == "microsoft"

    def test_enum_count(self) -> None:
        assert len(IdentityProviderType) == 5


class TestIdentityProviderModel:
    """Tests for IdentityProvider SQLAlchemy model definition."""

    def test_tablename(self) -> None:
        assert IdentityProvider.__tablename__ == "identity_providers"

    def test_core_fields(self) -> None:
        tid = uuid.uuid4()
        idp = IdentityProvider(
            tenant_id=tid,
            name="Acme SSO",
            provider_type=IdentityProviderType.OIDC,
            client_id="acme-client-id",
            scopes=["openid", "profile", "email"],
            is_active=True,
            is_default=False,
            auto_provision=False,
            allow_linking=True,
            display_order=0,
        )
        assert idp.tenant_id == tid
        assert idp.name == "Acme SSO"
        assert idp.provider_type == IdentityProviderType.OIDC
        assert idp.client_id == "acme-client-id"

    def test_oidc_endpoints(self) -> None:
        idp = IdentityProvider(
            tenant_id=uuid.uuid4(),
            name="Test",
            provider_type=IdentityProviderType.OIDC,
            client_id="c",
            discovery_url="https://idp.example.com/.well-known/openid-configuration",
            authorization_endpoint="https://idp.example.com/authorize",
            token_endpoint="https://idp.example.com/token",
            userinfo_endpoint="https://idp.example.com/userinfo",
            jwks_uri="https://idp.example.com/.well-known/jwks.json",
            scopes=["openid"],
            is_active=True,
            is_default=False,
            auto_provision=False,
            allow_linking=True,
            display_order=0,
        )
        assert idp.discovery_url is not None
        assert idp.jwks_uri is not None
        assert "jwks" in (idp.jwks_uri or "")

    def test_encrypted_secret(self) -> None:
        idp = IdentityProvider(
            tenant_id=uuid.uuid4(),
            name="Test",
            provider_type=IdentityProviderType.GITHUB,
            client_id="c",
            client_secret_encrypted=b"\x00\x01\x02encrypted",
            scopes=["openid"],
            is_active=True,
            is_default=False,
            auto_provision=False,
            allow_linking=True,
            display_order=0,
        )
        assert isinstance(idp.client_secret_encrypted, bytes)

    def test_attribute_mapping(self) -> None:
        idp = IdentityProvider(
            tenant_id=uuid.uuid4(),
            name="Test",
            provider_type=IdentityProviderType.OIDC,
            client_id="c",
            attribute_mapping={"email": "mail", "name": "displayName"},
            scopes=["openid"],
            is_active=True,
            is_default=False,
            auto_provision=False,
            allow_linking=True,
            display_order=0,
        )
        assert idp.attribute_mapping is not None
        assert idp.attribute_mapping["email"] == "mail"

    def test_allowed_domains(self) -> None:
        idp = IdentityProvider(
            tenant_id=uuid.uuid4(),
            name="Test",
            provider_type=IdentityProviderType.OIDC,
            client_id="c",
            allowed_domains=["acme.com", "acme.org"],
            scopes=["openid"],
            is_active=True,
            is_default=False,
            auto_provision=False,
            allow_linking=True,
            display_order=0,
        )
        assert idp.allowed_domains is not None
        assert "acme.com" in idp.allowed_domains

    def test_ui_display_fields(self) -> None:
        idp = IdentityProvider(
            tenant_id=uuid.uuid4(),
            name="Google",
            provider_type=IdentityProviderType.GOOGLE,
            client_id="c",
            icon_url="https://cdn.example.com/google.svg",
            button_text="Sign in with Google",
            display_order=1,
            scopes=["openid"],
            is_active=True,
            is_default=False,
            auto_provision=False,
            allow_linking=True,
        )
        assert idp.icon_url == "https://cdn.example.com/google.svg"
        assert idp.button_text == "Sign in with Google"
        assert idp.display_order == 1

    def test_settings_flags(self) -> None:
        idp = IdentityProvider(
            tenant_id=uuid.uuid4(),
            name="Test",
            provider_type=IdentityProviderType.OIDC,
            client_id="c",
            is_active=True,
            is_default=True,
            auto_provision=True,
            allow_linking=False,
            scopes=["openid"],
            display_order=0,
        )
        assert idp.is_default is True
        assert idp.auto_provision is True
        assert idp.allow_linking is False

    def test_tenant_id_indexed(self) -> None:
        col = IdentityProvider.__table__.c.tenant_id
        assert col.index is True

    def test_repr(self) -> None:
        idp = IdentityProvider(
            tenant_id=uuid.uuid4(),
            name="Okta",
            provider_type=IdentityProviderType.OIDC,
            client_id="c",
            scopes=["openid"],
            is_active=True,
            is_default=False,
            auto_provision=False,
            allow_linking=True,
            display_order=0,
        )
        r = repr(idp)
        assert "Okta" in r
        assert "oidc" in r

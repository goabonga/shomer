# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""IdentityProvider model for federated SSO."""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    Boolean,
    Enum,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from shomer.models.federated_identity import FederatedIdentity
    from shomer.models.tenant import Tenant

from shomer.core.database import Base, TimestampMixin, UUIDMixin


class IdentityProviderType(str, enum.Enum):
    """Type of external identity provider.

    Attributes
    ----------
    OIDC
        Generic OIDC (Keycloak, Auth0, Okta, Azure AD).
    SAML
        SAML 2.0.
    GOOGLE
        Google OAuth2.
    GITHUB
        GitHub OAuth2.
    MICROSOFT
        Microsoft / Azure AD.
    """

    OIDC = "oidc"
    SAML = "saml"
    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "microsoft"


class IdentityProvider(Base, UUIDMixin, TimestampMixin):
    """External identity provider configuration for a tenant.

    Stores OIDC/SAML endpoints, client credentials (encrypted),
    attribute mapping, domain restrictions, and UI display settings.

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    tenant_id : uuid.UUID
        Foreign key to the tenant.
    name : str
        Human-readable provider name (e.g. "Acme SSO").
    provider_type : IdentityProviderType
        Provider protocol type.
    discovery_url : str or None
        OIDC discovery endpoint (``/.well-known/openid-configuration``).
    authorization_endpoint : str or None
        OAuth2 authorization URL.
    token_endpoint : str or None
        OAuth2 token URL.
    userinfo_endpoint : str or None
        OIDC userinfo URL.
    jwks_uri : str or None
        JWKS endpoint for signature verification.
    client_id : str
        OAuth2 client identifier.
    client_secret_encrypted : bytes or None
        AES-256-GCM encrypted client secret.
    scopes : list[str]
        Scopes to request (default: openid, profile, email).
    attribute_mapping : dict or None
        External claim → internal field mapping.
    allowed_domains : list[str] or None
        Email domain restrictions for this IdP.
    is_active : bool
        Whether this IdP is enabled.
    is_default : bool
        Whether this is the default IdP for the tenant (auto-redirect).
    auto_provision : bool
        Auto-create user and add to tenant on first login.
    allow_linking : bool
        Allow linking existing accounts to this IdP.
    icon_url : str or None
        Icon URL for the login button.
    button_text : str or None
        Custom button text (e.g. "Sign in with Acme SSO").
    display_order : int
        Sort order on the login page.
    tenant : Tenant
        The associated tenant.
    federated_identities : list[FederatedIdentity]
        User identities linked via this provider.
    created_at : datetime
        Row creation timestamp (from TimestampMixin).
    updated_at : datetime
        Last update timestamp (from TimestampMixin).
    """

    __tablename__ = "identity_providers"
    __table_args__ = (
        Index("ix_identity_providers_tenant_active", "tenant_id", "is_active"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_type: Mapped[IdentityProviderType] = mapped_column(
        Enum(IdentityProviderType, name="identity_provider_type", native_enum=False),
        nullable=False,
    )

    # OIDC configuration
    discovery_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    authorization_endpoint: Mapped[str | None] = mapped_column(
        String(2048), nullable=True
    )
    token_endpoint: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    userinfo_endpoint: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    jwks_uri: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # Client credentials
    client_id: Mapped[str] = mapped_column(String(255), nullable=False)
    client_secret_encrypted: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True
    )

    # Scopes and mapping
    scopes: Mapped[list] = mapped_column(  # type: ignore[type-arg]
        JSON,
        nullable=False,
        default=lambda: ["openid", "profile", "email"],
    )
    attribute_mapping: Mapped[dict | None] = mapped_column(  # type: ignore[type-arg]
        JSON, nullable=True, default=dict
    )
    allowed_domains: Mapped[list | None] = mapped_column(  # type: ignore[type-arg]
        JSON, nullable=True
    )

    # Settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_provision: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_linking: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # UI display
    icon_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    button_text: Mapped[str | None] = mapped_column(String(100), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    tenant: Mapped[Tenant] = relationship(back_populates="identity_providers")
    federated_identities: Mapped[list[FederatedIdentity]] = relationship(
        back_populates="identity_provider",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<IdentityProvider name={self.name} type={self.provider_type.value}>"

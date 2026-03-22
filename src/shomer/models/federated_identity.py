# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""FederatedIdentity model linking users to external identity providers."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from shomer.models.identity_provider import IdentityProvider
    from shomer.models.user import User

from shomer.core.database import Base, TimestampMixin, UUIDMixin


class FederatedIdentity(Base, UUIDMixin, TimestampMixin):
    """Link between a local user and an external identity from an IdP.

    Stores the external subject identifier, email, username, and the
    raw claims from the IdP for audit purposes.

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    user_id : uuid.UUID
        Foreign key to the local user.
    identity_provider_id : uuid.UUID
        Foreign key to the identity provider.
    external_subject : str
        The ``sub`` claim from the external IdP (unique per provider).
    external_email : str or None
        Email from the external IdP.
    external_username : str or None
        Username/display name from the external IdP.
    raw_claims : dict or None
        Full claims from the IdP token for debugging/audit.
    linked_at : datetime
        When the user linked their account to this IdP.
    last_login_at : datetime or None
        Last federated login timestamp.
    user : User
        The local user.
    identity_provider : IdentityProvider
        The external identity provider.
    created_at : datetime
        Row creation timestamp (from TimestampMixin).
    updated_at : datetime
        Last update timestamp (from TimestampMixin).
    """

    __tablename__ = "federated_identities"
    __table_args__ = (
        UniqueConstraint(
            "identity_provider_id",
            "external_subject",
            name="uq_federated_identities_idp_subject",
        ),
        Index(
            "ix_federated_identities_user_idp",
            "user_id",
            "identity_provider_id",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    identity_provider_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("identity_providers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # External identity
    external_subject: Mapped[str] = mapped_column(String(255), nullable=False)
    external_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_claims: Mapped[dict | None] = mapped_column(  # type: ignore[type-arg]
        JSON, nullable=True
    )

    # Timestamps
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped[User] = relationship()
    identity_provider: Mapped[IdentityProvider] = relationship(
        back_populates="federated_identities"
    )

    def __repr__(self) -> str:
        return (
            f"<FederatedIdentity user={self.user_id} "
            f"provider={self.identity_provider_id} sub={self.external_subject}>"
        )

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Add identity_providers and federated_identities tables.

Revision ID: 0022
Revises: 0021
Create Date: 2026-03-22

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0022"
down_revision: Union[str, None] = "0021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create identity_providers and federated_identities tables."""
    op.create_table(
        "identity_providers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("provider_type", sa.String(20), nullable=False),
        # OIDC endpoints
        sa.Column("discovery_url", sa.String(2048), nullable=True),
        sa.Column("authorization_endpoint", sa.String(2048), nullable=True),
        sa.Column("token_endpoint", sa.String(2048), nullable=True),
        sa.Column("userinfo_endpoint", sa.String(2048), nullable=True),
        sa.Column("jwks_uri", sa.String(2048), nullable=True),
        # Client credentials
        sa.Column("client_id", sa.String(255), nullable=False),
        sa.Column("client_secret_encrypted", sa.LargeBinary(), nullable=True),
        # Scopes and mapping
        sa.Column(
            "scopes",
            sa.JSON(),
            nullable=False,
            server_default='["openid", "profile", "email"]',
        ),
        sa.Column("attribute_mapping", sa.JSON(), nullable=True),
        sa.Column("allowed_domains", sa.JSON(), nullable=True),
        # Settings
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "auto_provision", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("allow_linking", sa.Boolean(), nullable=False, server_default="true"),
        # UI display
        sa.Column("icon_url", sa.String(2048), nullable=True),
        sa.Column("button_text", sa.String(100), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_identity_providers_tenant_id", "identity_providers", ["tenant_id"]
    )
    op.create_index(
        "ix_identity_providers_tenant_active",
        "identity_providers",
        ["tenant_id", "is_active"],
    )

    op.create_table(
        "federated_identities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("identity_provider_id", sa.Uuid(), nullable=False),
        sa.Column("external_subject", sa.String(255), nullable=False),
        sa.Column("external_email", sa.String(255), nullable=True),
        sa.Column("external_username", sa.String(255), nullable=True),
        sa.Column("raw_claims", sa.JSON(), nullable=True),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["identity_provider_id"],
            ["identity_providers.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "identity_provider_id",
            "external_subject",
            name="uq_federated_identities_idp_subject",
        ),
    )
    op.create_index(
        "ix_federated_identities_user_id", "federated_identities", ["user_id"]
    )
    op.create_index(
        "ix_federated_identities_idp_id",
        "federated_identities",
        ["identity_provider_id"],
    )
    op.create_index(
        "ix_federated_identities_user_idp",
        "federated_identities",
        ["user_id", "identity_provider_id"],
    )


def downgrade() -> None:
    """Drop federation tables."""
    op.drop_table("federated_identities")
    op.drop_table("identity_providers")

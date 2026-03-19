# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Add oauth2_clients table.

Revision ID: 0008
Revises: 0007
Create Date: 2026-03-19

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create oauth2_clients table."""
    op.create_table(
        "oauth2_clients",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.String(255), nullable=False),
        sa.Column("client_secret_hash", sa.Text(), nullable=True),
        sa.Column("client_name", sa.String(255), nullable=False),
        sa.Column(
            "client_type",
            sa.String(12),
            nullable=False,
            server_default="confidential",
        ),
        sa.Column("redirect_uris", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("grant_types", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("response_types", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("scopes", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("logo_uri", sa.String(2048), nullable=True),
        sa.Column("tos_uri", sa.String(2048), nullable=True),
        sa.Column("policy_uri", sa.String(2048), nullable=True),
        sa.Column("contacts", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_oauth2_clients")),
        sa.UniqueConstraint("client_id", name=op.f("uq_oauth2_clients_client_id")),
    )
    op.create_index(
        op.f("ix_oauth2_clients_client_id"), "oauth2_clients", ["client_id"]
    )


def downgrade() -> None:
    """Drop oauth2_clients table."""
    op.drop_table("oauth2_clients")

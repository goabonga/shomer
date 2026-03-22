# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Add trust policy: tenant fields + tenant_trusted_sources + user registration_tenant_id.

Revision ID: 0021
Revises: 0020
Create Date: 2026-03-22

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0021"
down_revision: Union[str, None] = "0020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add trust policy fields and tables."""
    # Add new columns to tenants
    op.add_column(
        "tenants",
        sa.Column("display_name", sa.String(255), nullable=False, server_default=""),
    )
    op.add_column(
        "tenants",
        sa.Column("is_platform", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "tenants",
        sa.Column("trust_mode", sa.String(20), nullable=False, server_default="none"),
    )

    # Add registration_tenant_id to users
    op.add_column(
        "users",
        sa.Column("registration_tenant_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_users_registration_tenant_id",
        "users",
        "tenants",
        ["registration_tenant_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_users_registration_tenant_id", "users", ["registration_tenant_id"]
    )

    # Create tenant_trusted_sources table
    op.create_table(
        "tenant_trusted_sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("trusted_tenant_id", sa.Uuid(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["trusted_tenant_id"], ["tenants.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "tenant_id", "trusted_tenant_id", name="uq_tenant_trusted_source"
        ),
    )
    op.create_index(
        "ix_tenant_trusted_sources_tenant_id",
        "tenant_trusted_sources",
        ["tenant_id"],
    )
    op.create_index(
        "ix_tenant_trusted_sources_trusted_tenant_id",
        "tenant_trusted_sources",
        ["trusted_tenant_id"],
    )


def downgrade() -> None:
    """Remove trust policy."""
    op.drop_table("tenant_trusted_sources")
    op.drop_index("ix_users_registration_tenant_id", table_name="users")
    op.drop_constraint("fk_users_registration_tenant_id", "users", type_="foreignkey")
    op.drop_column("users", "registration_tenant_id")
    op.drop_column("tenants", "trust_mode")
    op.drop_column("tenants", "is_platform")
    op.drop_column("tenants", "display_name")

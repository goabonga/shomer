# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Add user_profiles table.

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-18

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create user_profiles table."""
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("given_name", sa.String(255), nullable=True),
        sa.Column("family_name", sa.String(255), nullable=True),
        sa.Column("middle_name", sa.String(255), nullable=True),
        sa.Column("nickname", sa.String(255), nullable=True),
        sa.Column("preferred_username", sa.String(255), nullable=True),
        sa.Column("profile_url", sa.String(2048), nullable=True),
        sa.Column("picture_url", sa.String(2048), nullable=True),
        sa.Column("website", sa.String(2048), nullable=True),
        sa.Column("gender", sa.String(50), nullable=True),
        sa.Column("birthdate", sa.String(10), nullable=True),
        sa.Column("zoneinfo", sa.String(50), nullable=True),
        sa.Column("locale", sa.String(10), nullable=True),
        sa.Column("address_formatted", sa.Text(), nullable=True),
        sa.Column("address_street", sa.String(500), nullable=True),
        sa.Column("address_locality", sa.String(255), nullable=True),
        sa.Column("address_region", sa.String(255), nullable=True),
        sa.Column("address_postal_code", sa.String(50), nullable=True),
        sa.Column("address_country", sa.String(100), nullable=True),
        sa.Column("phone_number", sa.String(50), nullable=True),
        sa.Column(
            "phone_number_verified",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_profiles")),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_profiles_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("user_id", name=op.f("uq_user_profiles_user_id")),
    )
    op.create_index(op.f("ix_user_profiles_user_id"), "user_profiles", ["user_id"])


def downgrade() -> None:
    """Drop user_profiles table."""
    op.drop_table("user_profiles")

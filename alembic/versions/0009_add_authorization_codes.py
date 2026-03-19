# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Add authorization_codes table.

Revision ID: 0009
Revises: 0008
Create Date: 2026-03-19

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create authorization_codes table."""
    op.create_table(
        "authorization_codes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(255), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.String(255), nullable=False),
        sa.Column("redirect_uri", sa.Text(), nullable=False),
        sa.Column("scopes", sa.Text(), nullable=False, server_default=""),
        sa.Column("nonce", sa.String(255), nullable=True),
        sa.Column("code_challenge", sa.String(128), nullable=True),
        sa.Column("code_challenge_method", sa.String(10), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_used", sa.Boolean(), nullable=False, server_default="false"),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_authorization_codes")),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_authorization_codes_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("code", name=op.f("uq_authorization_codes_code")),
    )
    op.create_index(
        op.f("ix_authorization_codes_code"),
        "authorization_codes",
        ["code"],
    )
    op.create_index(
        op.f("ix_authorization_codes_user_id"),
        "authorization_codes",
        ["user_id"],
    )
    op.create_index(
        op.f("ix_authorization_codes_client_id"),
        "authorization_codes",
        ["client_id"],
    )


def downgrade() -> None:
    """Drop authorization_codes table."""
    op.drop_table("authorization_codes")

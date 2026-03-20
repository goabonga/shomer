# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Add device_codes table for RFC 8628.

Revision ID: 0013
Revises: 0012
Create Date: 2026-03-21

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create device_codes table."""
    op.create_table(
        "device_codes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("device_code", sa.String(255), nullable=False),
        sa.Column("user_code", sa.String(16), nullable=False),
        sa.Column("client_id", sa.String(255), nullable=False),
        sa.Column("scopes", sa.Text(), nullable=False, server_default=""),
        sa.Column("verification_uri", sa.String(2048), nullable=False),
        sa.Column("verification_uri_complete", sa.String(2048), nullable=True),
        sa.Column("interval", sa.Integer(), nullable=False, server_default="5"),
        sa.Column(
            "status",
            sa.String(10),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_device_codes")),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_device_codes_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("device_code", name=op.f("uq_device_codes_device_code")),
        sa.UniqueConstraint("user_code", name=op.f("uq_device_codes_user_code")),
    )
    op.create_index(
        op.f("ix_device_codes_device_code"), "device_codes", ["device_code"]
    )
    op.create_index(op.f("ix_device_codes_user_code"), "device_codes", ["user_code"])


def downgrade() -> None:
    """Drop device_codes table."""
    op.drop_table("device_codes")

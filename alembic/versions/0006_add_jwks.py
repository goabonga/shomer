# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Add jwks table.

Revision ID: 0006
Revises: 0005
Create Date: 2026-03-18

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create jwks table."""
    op.create_table(
        "jwks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("kid", sa.String(255), nullable=False),
        sa.Column("algorithm", sa.String(20), nullable=False),
        sa.Column("public_key", sa.Text(), nullable=False),
        sa.Column("private_key_enc", sa.LargeBinary(), nullable=False),
        sa.Column(
            "status",
            sa.String(7),
            nullable=False,
            server_default="active",
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_jwks")),
        sa.UniqueConstraint("kid", name=op.f("uq_jwks_kid")),
    )
    op.create_index(op.f("ix_jwks_kid"), "jwks", ["kid"])
    op.create_index(op.f("ix_jwks_status"), "jwks", ["status"])


def downgrade() -> None:
    """Drop jwks table."""
    op.drop_table("jwks")

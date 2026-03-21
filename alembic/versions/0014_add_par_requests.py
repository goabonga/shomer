# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Add par_requests table for RFC 9126.

Revision ID: 0014
Revises: 0013
Create Date: 2026-03-21

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create par_requests table."""
    op.create_table(
        "par_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("request_uri", sa.String(255), nullable=False),
        sa.Column("client_id", sa.String(255), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_par_requests")),
        sa.UniqueConstraint("request_uri", name=op.f("uq_par_requests_request_uri")),
    )
    op.create_index(
        op.f("ix_par_requests_request_uri"), "par_requests", ["request_uri"]
    )


def downgrade() -> None:
    """Drop par_requests table."""
    op.drop_table("par_requests")

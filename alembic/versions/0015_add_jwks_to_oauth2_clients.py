# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Add jwks column to oauth2_clients for RFC 9101 JAR support.

Revision ID: 0015
Revises: 0014
Create Date: 2026-03-21

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: Union[str, None] = "0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add jwks JSON column to oauth2_clients."""
    op.add_column(
        "oauth2_clients",
        sa.Column("jwks", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    """Remove jwks column from oauth2_clients."""
    op.drop_column("oauth2_clients", "jwks")

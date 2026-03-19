# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Add token_endpoint_auth_method to oauth2_clients.

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
    """Add token_endpoint_auth_method column."""
    op.add_column(
        "oauth2_clients",
        sa.Column(
            "token_endpoint_auth_method",
            sa.String(20),
            nullable=False,
            server_default="client_secret_basic",
        ),
    )


def downgrade() -> None:
    """Remove token_endpoint_auth_method column."""
    op.drop_column("oauth2_clients", "token_endpoint_auth_method")

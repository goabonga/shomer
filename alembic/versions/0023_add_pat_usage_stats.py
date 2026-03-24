# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Add use_count and last_used_ip columns to personal_access_tokens.

Revision ID: 0023
Revises: 0022
Create Date: 2026-03-24

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0023"
down_revision: Union[str, None] = "0022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add use_count and last_used_ip to personal_access_tokens."""
    op.add_column(
        "personal_access_tokens",
        sa.Column("use_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "personal_access_tokens",
        sa.Column("last_used_ip", sa.String(45), nullable=True),
    )


def downgrade() -> None:
    """Remove use_count and last_used_ip from personal_access_tokens."""
    op.drop_column("personal_access_tokens", "last_used_ip")
    op.drop_column("personal_access_tokens", "use_count")

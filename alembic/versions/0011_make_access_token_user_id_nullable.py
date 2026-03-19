# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Make access_token.user_id nullable for client_credentials grants.

Revision ID: 0011
Revises: 0010
Create Date: 2026-03-19

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Allow NULL user_id on access_tokens for M2M tokens."""
    op.alter_column(
        "access_tokens",
        "user_id",
        existing_type=sa.Uuid(),
        nullable=True,
    )


def downgrade() -> None:
    """Restore NOT NULL constraint on access_tokens.user_id."""
    op.alter_column(
        "access_tokens",
        "user_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )

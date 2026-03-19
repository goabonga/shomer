# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Convert oauth2_clients JSON columns from text to json type.

The original migration (0008) created these as text columns, but the
SQLAlchemy model uses sa.JSON. PostgreSQL needs native json/jsonb for
proper serialization/deserialization.

Revision ID: 0012
Revises: 0011
Create Date: 2026-03-19

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_JSON_COLUMNS = [
    "redirect_uris",
    "grant_types",
    "response_types",
    "scopes",
    "contacts",
]


def upgrade() -> None:
    """Convert text columns to json using USING clause."""
    for col in _JSON_COLUMNS:
        # Drop default first (text default can't auto-cast to json)
        op.execute(
            sa.text(f"ALTER TABLE oauth2_clients ALTER COLUMN {col} DROP DEFAULT")
        )
        op.execute(
            sa.text(
                f"ALTER TABLE oauth2_clients "
                f"ALTER COLUMN {col} TYPE json USING {col}::json"
            )
        )
        # Restore default as JSON
        op.execute(
            sa.text(
                f"ALTER TABLE oauth2_clients ALTER COLUMN {col} SET DEFAULT '[]'::json"
            )
        )


def downgrade() -> None:
    """Convert json columns back to text."""
    for col in _JSON_COLUMNS:
        op.execute(
            sa.text(
                f"ALTER TABLE oauth2_clients "
                f"ALTER COLUMN {col} TYPE text USING {col}::text"
            )
        )

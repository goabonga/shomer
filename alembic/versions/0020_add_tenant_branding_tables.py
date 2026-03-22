# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Add tenant_brandings and tenant_templates tables.

Revision ID: 0020
Revises: 0019
Create Date: 2026-03-22

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0020"
down_revision: Union[str, None] = "0019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create tenant_brandings and tenant_templates tables."""
    op.create_table(
        "tenant_brandings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        # Logo and favicon
        sa.Column("logo_url", sa.String(2048), nullable=True),
        sa.Column("logo_dark_url", sa.String(2048), nullable=True),
        sa.Column("favicon_url", sa.String(2048), nullable=True),
        # Colors
        sa.Column("primary_color", sa.String(7), nullable=True),
        sa.Column("secondary_color", sa.String(7), nullable=True),
        sa.Column("accent_color", sa.String(7), nullable=True),
        sa.Column("background_color", sa.String(7), nullable=True),
        sa.Column("surface_color", sa.String(7), nullable=True),
        sa.Column("text_color", sa.String(7), nullable=True),
        sa.Column("text_muted_color", sa.String(7), nullable=True),
        sa.Column("error_color", sa.String(7), nullable=True),
        sa.Column("success_color", sa.String(7), nullable=True),
        sa.Column("border_color", sa.String(7), nullable=True),
        sa.Column("warning_color", sa.String(7), nullable=True),
        sa.Column("info_color", sa.String(7), nullable=True),
        # Typography
        sa.Column("font_family", sa.String(500), nullable=True),
        sa.Column("font_url", sa.String(2048), nullable=True),
        # Custom code
        sa.Column("custom_css", sa.Text(), nullable=True),
        sa.Column("custom_js", sa.Text(), nullable=True),
        # Settings
        sa.Column(
            "show_powered_by", sa.Boolean(), nullable=False, server_default="true"
        ),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id"),
    )
    op.create_index("ix_tenant_brandings_tenant_id", "tenant_brandings", ["tenant_id"])

    op.create_table(
        "tenant_templates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("template_name", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "tenant_id", "template_name", name="uq_tenant_template_name"
        ),
    )
    op.create_index("ix_tenant_templates_tenant_id", "tenant_templates", ["tenant_id"])


def downgrade() -> None:
    """Drop tenant branding tables."""
    op.drop_table("tenant_templates")
    op.drop_table("tenant_brandings")

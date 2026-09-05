# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""The Alembic environment.

The revisions live here rather than in `shomer-lib` so a service that only
needs the models never installs Alembic or the revision tree with them.

The URL is resolved rather than configured, in this order: `-x url=...`,
then `sqlalchemy.url` from the ini, then the settings the rest of the
platform reads. Nothing is written into the checkout, so a clone carries
no credentials and cannot be pointed at production by an unedited file.
"""

from __future__ import annotations

from alembic import context
from sqlalchemy import engine_from_config, pool

from shomer_lib.models import Base
from shomer_lib.settings import EnvSettings

config = context.config
target_metadata = Base.metadata


def database_url() -> str:
    """Resolve the URL to migrate, most explicit source first."""
    overrides = context.get_x_argument(as_dictionary=True)
    if "url" in overrides:
        return str(overrides["url"])
    configured = config.get_main_option("sqlalchemy.url")
    if configured:
        return configured
    return EnvSettings.from_env().database_url


def run_migrations_offline() -> None:
    """Emit SQL to stdout instead of running it against a connection."""
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Type changes are invisible to autogenerate without this, so a
        # column that widened in the models stays narrow in the database
        # and the mismatch only surfaces on the row that overflows it.
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run the migrations against a live connection."""
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = database_url()
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        # NullPool: a migration run is a single short-lived process. A
        # real pool would hold connections open past the last revision
        # and delay the exit for no benefit.
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():  # pragma: no cover - selected by the alembic CLI
    run_migrations_offline()
else:  # pragma: no cover - exercised through the runner, not by import
    run_migrations_online()

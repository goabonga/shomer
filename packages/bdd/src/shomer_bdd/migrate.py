# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""Apply the pending migrations.

The `shomer-bdd` console script. It locates the revisions inside the
installed package rather than relative to the working directory, so it
behaves the same run from a checkout, a container or a service unit.

It only ever moves the schema to a revision. It does not create, drop or
seed a database — a migration runner that can also destroy one is a
migration runner nobody can safely give production credentials to.
"""

from __future__ import annotations

import sys
from importlib.resources import files

from alembic import command
from alembic.config import Config


def alembic_config() -> Config:
    """Alembic config pointing at the revisions shipped in this package."""
    config = Config()
    config.set_main_option("script_location", str(files("shomer_bdd") / "migrations"))
    return config


def upgrade(revision: str = "head") -> None:
    """Apply pending migrations up to `revision`."""
    command.upgrade(alembic_config(), revision)


def main(argv: list[str] | None = None) -> None:
    """Console-script entrypoint (`shomer-bdd [REVISION]`)."""
    args = sys.argv[1:] if argv is None else argv
    upgrade(args[0] if args else "head")

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""The `shomer` command group.

The container is handed to the group as Click's context object and reaches
each command through `@click.pass_obj`. That is what makes `shomer config`
worth running: it reports what the container actually resolved in this
process and this environment, not what a configuration file claims.
"""

from __future__ import annotations

import click
from sqlalchemy import make_url, text
from tripack_container import Container

from shomer_lib.contracts import Clock, Database, Settings

from . import __version__


@click.group(name="shomer", help="Inspect a Shomer instance.")
def cli() -> None:
    """Root group; subcommands receive the container via `@click.pass_obj`."""


@cli.command()
def version() -> None:
    """Print the installed version."""
    click.echo(__version__)


@cli.command()
@click.pass_obj
def config(container: Container) -> None:
    """Print the settings this process resolved."""
    settings = container.resolve(Settings)
    click.echo(f"issuer       = {settings.issuer}")
    # The URL can carry a password. Rendering it through SQLAlchemy's own
    # repr keeps it masked, so the output is safe to paste into an issue —
    # which is exactly what someone diagnosing a connection problem does.
    click.echo(f"database_url = {make_url(settings.database_url)}")


@cli.command(name="check-db")
@click.pass_obj
def check_db(container: Container) -> None:
    """Open a connection and report how long it took.

    `SELECT 1` rather than a query against a table: this answers "can this
    process reach its database", which is a different question from
    "has the schema been migrated", and conflating the two makes a
    pre-migration instance look unreachable.
    """
    clock = container.resolve(Clock)
    database = container.resolve(Database)
    started = clock.now()
    with database.session() as session:
        session.execute(text("select 1"))
    click.echo(f"ok ({(clock.now() - started) * 1000:.1f} ms)")

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""Tests for the migration runner and its Alembic environment.

Every test drives real Alembic against a throwaway SQLite file, so the
revision tree, `env.py` and the runner are exercised together — a runner
that passes in isolation while the environment cannot resolve a URL is a
runner that fails only in production.
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

import pytest
from alembic import command
from sqlalchemy import create_engine, inspect

from shomer_bdd.migrate import alembic_config, main, upgrade

EXPECTED_TABLES = {"users", "clients"}


@pytest.fixture
def database_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    url = f"sqlite+pysqlite:///{tmp_path / 'shomer.db'}"
    monkeypatch.setenv("SHOMER_DATABASE_URL", url)
    return url


def tables_of(url: str) -> set[str]:
    engine = create_engine(url)
    try:
        return set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_config_points_at_the_packaged_revisions() -> None:
    # Resolved from the installed package, not relative to the working
    # directory: the runner has to behave the same from a checkout, a
    # container and a service unit.
    location = alembic_config().get_main_option("script_location")
    assert location is not None
    assert Path(location).joinpath("env.py").is_file()


def test_upgrade_creates_the_schema(database_url: str) -> None:
    upgrade()
    assert tables_of(database_url) >= EXPECTED_TABLES


def test_main_without_arguments_goes_to_head(database_url: str) -> None:
    main([])
    assert tables_of(database_url) >= EXPECTED_TABLES


def test_main_reads_the_revision_from_argv(
    database_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("sys.argv", ["shomer-bdd", "head"])
    main()
    assert tables_of(database_url) >= EXPECTED_TABLES


def test_main_accepts_an_explicit_revision(database_url: str) -> None:
    main(["base"])
    # `base` is "before the first revision", so nothing is applied and the
    # only table is Alembic's own bookkeeping.
    assert not EXPECTED_TABLES & tables_of(database_url)


def test_an_x_argument_overrides_the_environment(
    tmp_path: Path, database_url: str
) -> None:
    # -x wins over everything, which is what makes it safe to point a run
    # at a scratch database without editing any file.
    override = f"sqlite+pysqlite:///{tmp_path / 'override.db'}"
    config = alembic_config()
    config.cmd_opts = Namespace(x=[f"url={override}"])
    command.upgrade(config, "head")
    assert tables_of(override) >= EXPECTED_TABLES
    assert not EXPECTED_TABLES & tables_of(database_url)


def test_a_configured_url_wins_over_the_environment(
    tmp_path: Path, database_url: str
) -> None:
    configured = f"sqlite+pysqlite:///{tmp_path / 'configured.db'}"
    config = alembic_config()
    config.set_main_option("sqlalchemy.url", configured)
    command.upgrade(config, "head")
    assert tables_of(configured) >= EXPECTED_TABLES
    assert not EXPECTED_TABLES & tables_of(database_url)


def test_offline_mode_emits_sql_instead_of_running_it(
    database_url: str, capsys: pytest.CaptureFixture[str]
) -> None:
    command.upgrade(alembic_config(), "head", sql=True)
    emitted = capsys.readouterr().out
    assert "CREATE TABLE users" in emitted
    # Nothing reached the database — that is the whole point of --sql.
    assert not EXPECTED_TABLES & tables_of(database_url)

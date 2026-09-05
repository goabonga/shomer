# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""Tests for the `shomer` command-line interface."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from click.testing import CliRunner
from tripack_container import Container

from shomer_cli import __version__
from shomer_cli.__main__ import main
from shomer_cli.cli import cli
from shomer_lib.contracts import Database
from shomer_lib.models import Base
from shomer_lib.module import build_container


@pytest.fixture(autouse=True)
def _isolated_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SHOMER_DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("SHOMER_ISSUER", "https://id.example.test")


@pytest.fixture
def container() -> Iterator[Container]:
    with build_container() as built:
        database = built.resolve(Database)
        Base.metadata.create_all(database.engine)  # type: ignore[attr-defined]
        yield built


def test_version_prints_the_installed_version() -> None:
    result = CliRunner().invoke(cli, ["version"])
    assert result.exit_code == 0
    assert result.output.strip() == __version__


def test_config_reports_what_the_container_resolved(container: Container) -> None:
    result = CliRunner().invoke(cli, ["config"], obj=container)
    assert result.exit_code == 0
    assert "issuer       = https://id.example.test" in result.output
    assert "database_url = sqlite+pysqlite:///:memory:" in result.output


def test_config_masks_the_database_password(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The output of a diagnostic command ends up pasted into issues.
    monkeypatch.setenv(
        "SHOMER_DATABASE_URL", "postgresql+psycopg://shomer:hunter2@db/shomer"
    )
    with build_container() as built:
        result = CliRunner().invoke(cli, ["config"], obj=built)
    assert result.exit_code == 0
    assert "hunter2" not in result.output
    assert "***" in result.output


def test_check_db_opens_a_connection(container: Container) -> None:
    result = CliRunner().invoke(cli, ["check-db"], obj=container)
    assert result.exit_code == 0
    assert result.output.startswith("ok (")


def test_check_db_does_not_require_a_migrated_schema() -> None:
    # "can this process reach its database" is a different question from
    # "has the schema been migrated"; conflating them makes a
    # pre-migration instance look unreachable.
    with build_container() as built:
        result = CliRunner().invoke(cli, ["check-db"], obj=built)
    assert result.exit_code == 0


def test_main_wires_the_container_into_the_group(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.argv", ["shomer", "config"])
    with pytest.raises(SystemExit) as exit_info:
        main()
    assert exit_info.value.code == 0
    assert "issuer       = https://id.example.test" in capsys.readouterr().out

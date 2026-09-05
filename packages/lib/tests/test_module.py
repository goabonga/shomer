# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""Tests for the shared dependency-injection module."""

import pytest
from tripack_container import ContainerBuilder

from shomer_lib.clock import SystemClock
from shomer_lib.contracts import Clock, Database, Settings
from shomer_lib.database import SqlAlchemyDatabase
from shomer_lib.module import ShomerModule, build_container
from shomer_lib.settings import EnvSettings


@pytest.fixture(autouse=True)
def _in_memory_database(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SHOMER_DATABASE_URL", "sqlite+pysqlite:///:memory:")


def test_the_contracts_resolve_to_the_default_implementations() -> None:
    with build_container() as container:
        assert isinstance(container.resolve(Settings), EnvSettings)
        assert isinstance(container.resolve(Clock), SystemClock)
        assert isinstance(container.resolve(Database), SqlAlchemyDatabase)


def test_the_shared_services_are_singletons() -> None:
    # The database owns a connection pool; resolving a second one would
    # open a second pool and leak it.
    with build_container() as container:
        assert container.resolve(Database) is container.resolve(Database)
        assert container.resolve(Clock) is container.resolve(Clock)


def test_the_database_is_built_from_the_injected_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SHOMER_DATABASE_URL", "sqlite+pysqlite:///:memory:")
    with build_container() as container:
        database = container.resolve(Database)
        assert isinstance(database, SqlAlchemyDatabase)
        assert database.engine.url.get_backend_name() == "sqlite"


def test_the_module_can_be_installed_on_a_builder_directly() -> None:
    container = ContainerBuilder().install(ShomerModule()).build()
    with container:
        assert isinstance(container.resolve(Settings), EnvSettings)


def test_closing_the_container_releases_the_connection_pool() -> None:
    # The container tears a singleton down by calling `close` on it. When
    # the connector spelled that `dispose`, nothing matched and the pool
    # outlived the process that opened it.
    container = build_container()
    database = container.resolve(Database)
    engine = database.engine  # type: ignore[attr-defined]
    with engine.connect():
        pass
    # `dispose()` discards the pool and installs a fresh one, so a
    # different pool object afterwards is the observable proof that the
    # container reached the connector at all.
    before = engine.pool
    container.close()
    assert engine.pool is not before

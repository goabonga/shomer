# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""The dependency-injection module every Shomer service installs.

This is the one place that decides which implementation answers which
contract. A service installs it and asks for `Settings`, `Clock` or
`Database`; it never names `EnvSettings`, `SystemClock` or
`SqlAlchemyDatabase`, so replacing one of them is an edit here and
nowhere else.
"""

from __future__ import annotations

from tripack_container import Container, ContainerBuilder
from tripack_contracts import Lifecycle

from shomer_lib.clock import SystemClock
from shomer_lib.contracts import Clock, Database, Settings
from shomer_lib.database import SqlAlchemyDatabase
from shomer_lib.settings import EnvSettings


class ShomerModule:
    """Bind the shared contracts to their default implementations."""

    def register(self, builder: ContainerBuilder) -> None:
        """Register the three shared singletons on `builder`."""
        # All three are SINGLETON: settings are read once, the clock is
        # stateless, and the database owns a connection pool that exists
        # to be shared. A TRANSIENT database would open a new pool per
        # resolution and leak every one of them.
        #
        # A Protocol token knocks `bind`'s overload resolution onto its
        # async variant, so mypy asks for an `Awaitable` nobody wants.
        # (The companion `type-abstract` complaint is turned off
        # workspace-wide — see [tool.mypy] in the root pyproject.)
        builder.bind(
            Settings,
            EnvSettings.from_env,  # type: ignore[arg-type]
            lifecycle=Lifecycle.SINGLETON,
        )
        builder.bind(
            Clock,
            SystemClock,  # type: ignore[arg-type]
            lifecycle=Lifecycle.SINGLETON,
        )
        builder.bind(
            Database,
            _make_database,  # type: ignore[arg-type]
            lifecycle=Lifecycle.SINGLETON,
            # The container resolves `Settings` from the factory's own
            # signature, so the wiring stays declarative rather than
            # reaching back into the container by hand.
            auto_inject=True,
        )


def _make_database(settings: Settings) -> Database:
    """Factory for the `Database` binding."""
    return SqlAlchemyDatabase(settings)


def build_container() -> Container:
    """Return a sealed container with the shared module installed.

    Services call this rather than assembling a builder themselves, so
    they all start from the same graph and a binding added here reaches
    every one of them.
    """
    return ContainerBuilder().install(ShomerModule()).build()

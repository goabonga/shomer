# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""The interfaces every Shomer service types against.

Nothing here has an implementation, and that is the point: a handler, a
command or a worker names one of these protocols, the container supplies
whatever is bound to it, and swapping the implementation — a fake clock in
a test, a different database — never reaches the caller.

The concrete side lives in :mod:`shomer_lib.clock`,
:mod:`shomer_lib.settings` and :mod:`shomer_lib.database`, and the wiring
that connects the two in :mod:`shomer_lib.module`.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import AbstractContextManager
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:  # pragma: no cover - import cycle guard for type checkers only
    from sqlalchemy.orm import Session


@runtime_checkable
class Clock(Protocol):
    """Wall-clock reader.

    An interface rather than a `datetime.now()` call because token
    lifetimes, session expiry and audit ordering all read the time, and a
    test that cannot move the clock cannot assert any of them.
    """

    def now(self) -> float:
        """Return the current POSIX timestamp."""
        ...


@runtime_checkable
class Settings(Protocol):
    """The configuration a service reads at runtime."""

    @property
    def issuer(self) -> str:
        """The `iss` claim, and the base URL of the discovery document."""
        ...

    @property
    def database_url(self) -> str:
        """SQLAlchemy URL of the backing database."""
        ...


@runtime_checkable
class Database(Protocol):
    """Access to the backing database."""

    def session(self) -> AbstractContextManager[Session]:
        """A unit of work: commits on success, rolls back on error."""
        ...

    def sessions(self) -> Iterator[Session]:
        """Yield one session and close it, leaving the commit to the caller."""
        ...

    def close(self) -> None:
        """Release the connection pool.

        Named `close` because that is the name the container looks for
        when it tears a singleton down. A connector that spells it
        anything else keeps its pool open for the life of the process.
        """
        ...

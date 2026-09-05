# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""The database connector.

One engine and one session factory per process, built from the injected
settings — so which backend a service talks to is a configuration
decision, not something written into a call site.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from shomer_lib.contracts import Settings


class SqlAlchemyDatabase:
    """Engine + session factory for one configured database."""

    def __init__(self, settings: Settings, **engine_kwargs: Any) -> None:
        self.engine: Engine = create_engine(settings.database_url, **engine_kwargs)
        # expire_on_commit=False so an object read inside a `session()`
        # block stays usable after the commit. Otherwise every attribute
        # access past the block re-queries a closed session and raises,
        # which reads as a bug in the caller rather than in the unit of
        # work it inherited.
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)

    @contextmanager
    def session(self) -> Iterator[Session]:
        """A unit of work: commit on success, roll back on error."""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def sessions(self) -> Iterator[Session]:
        """Yield one session and close it, leaving the commit to the caller.

        The rollback on the error path is what makes this safe to pool. A
        session whose transaction has already failed goes back to the pool
        in that state, and the next caller to borrow it meets
        `PendingRollbackError` on its first statement — reported against a
        request that did nothing wrong.
        """
        session = self.session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self) -> None:
        """Release the connection pool.

        The name is load-bearing: the container tears a singleton down by
        calling `close` on it, so spelling this `dispose` left the pool
        open for the life of the process and surfaced only as sockets
        that outlived the command that opened them.
        """
        self.engine.dispose()

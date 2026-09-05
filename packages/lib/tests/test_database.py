# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""Tests for the database connector."""

import pytest
from sqlalchemy import select, text

from shomer_lib.database import SqlAlchemyDatabase
from shomer_lib.models import Base, User
from shomer_lib.settings import EnvSettings


@pytest.fixture
def database() -> SqlAlchemyDatabase:
    db = SqlAlchemyDatabase(EnvSettings(database_url="sqlite+pysqlite:///:memory:"))
    Base.metadata.create_all(db.engine)
    return db


def _user(subject: str) -> User:
    return User(
        subject=subject,
        email=f"{subject}@example.test",
        password_hash="x",
        created_at=0.0,
    )


def test_session_commits_on_success(database: SqlAlchemyDatabase) -> None:
    with database.session() as session:
        session.add(_user("alice"))
    with database.session() as session:
        assert session.scalars(select(User)).one().subject == "alice"


def test_session_rolls_back_on_error(database: SqlAlchemyDatabase) -> None:
    with pytest.raises(RuntimeError), database.session() as session:
        session.add(_user("bob"))
        raise RuntimeError("boom")
    with database.session() as session:
        assert session.scalars(select(User)).all() == []


def test_sessions_leaves_the_commit_to_the_caller(
    database: SqlAlchemyDatabase,
) -> None:
    generator = database.sessions()
    session = next(generator)
    session.add(_user("carol"))
    # No commit — closing the session must discard the insert.
    generator.close()
    with database.session() as verify:
        assert verify.scalars(select(User)).all() == []


def test_sessions_rolls_back_before_returning_to_the_pool(
    database: SqlAlchemyDatabase,
) -> None:
    # Without the rollback the session goes back to the pool mid-failed
    # transaction, and the next caller to borrow it meets
    # PendingRollbackError on a request that did nothing wrong.
    generator = database.sessions()
    session = next(generator)
    session.add(_user("dave"))
    with pytest.raises(RuntimeError):
        generator.throw(RuntimeError("boom"))
    assert not session.in_transaction()


def test_close_releases_the_pool(database: SqlAlchemyDatabase) -> None:
    database.close()
    # A disposed engine builds a fresh pool on the next use rather than
    # failing. Asserted with a bare statement, not a query against a
    # table: an in-memory SQLite database lives inside its connection, so
    # dropping the pool drops the schema with it.
    with database.session() as session:
        assert session.execute(text("select 1")).scalar_one() == 1

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Async and sync SQLAlchemy database setup, base model and mixins."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from shomer.core.settings import get_settings

# Naming convention for constraints (Alembic-friendly)
convention: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """SQLAlchemy declarative base with naming convention.

    Attributes
    ----------
    metadata : MetaData
        Metadata with Alembic-friendly naming convention for constraints.
    """

    metadata = MetaData(naming_convention=convention)


class UUIDMixin:
    """Mixin that adds a UUID primary key column.

    Attributes
    ----------
    id : uuid.UUID
        Auto-generated UUID4 primary key.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    """Mixin that adds created_at and updated_at columns.

    Attributes
    ----------
    created_at : datetime
        Row creation timestamp, set by the database server.
    updated_at : datetime
        Last update timestamp, refreshed on every update.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


settings = get_settings()

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)

_sync_session_factory: object | None = None


def sync_session() -> Any:
    """Return a synchronous session for Celery tasks (lazy init).

    Returns
    -------
    Session
        A synchronous SQLAlchemy session context manager.
    """
    global _sync_session_factory  # noqa: PLW0603
    if _sync_session_factory is None:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        _sync_url = settings.database_url.replace("+asyncpg", "").replace(
            "postgresql+asyncpg", "postgresql"
        )
        _sync_engine = create_engine(_sync_url, echo=False)
        _sync_session_factory = sessionmaker(_sync_engine, expire_on_commit=False)
    return _sync_session_factory()  # type: ignore[operator]


async def get_db() -> AsyncIterator[AsyncSession]:  # pragma: no cover
    """Yield an async database session."""
    async with async_session() as session:
        yield session

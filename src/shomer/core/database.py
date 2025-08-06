# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Async SQLAlchemy database setup."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from shomer.core.settings import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


async def get_db() -> AsyncIterator[AsyncSession]:  # pragma: no cover
    """Yield an async database session."""
    async with async_session() as session:
        yield session

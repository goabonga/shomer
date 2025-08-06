# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

from shomer.core.database import Base, async_session, engine


def test_engine_url() -> None:
    assert "postgresql+asyncpg" in str(engine.url)


def test_async_session_factory() -> None:
    assert async_session is not None


def test_base_metadata() -> None:
    assert Base.metadata is not None

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for FastAPI dependency injection helpers."""

import asyncio
import inspect
from typing import get_type_hints

from fastapi.params import Depends as DependsClass
from sqlalchemy.ext.asyncio import AsyncSession

from shomer.core.settings import Settings
from shomer.deps import (
    Config,
    DbSession,
    TenantId,
    get_config,
    get_current_tenant,
    get_db,
)


class TestGetDb:
    """Tests for get_db dependency."""

    def test_is_async_generator(self) -> None:
        assert asyncio.iscoroutinefunction(get_db) or inspect.isasyncgenfunction(get_db)

    def test_yields_async_session(self) -> None:
        async def _run() -> None:
            async for session in get_db():
                assert isinstance(session, AsyncSession)

        asyncio.run(_run())


class TestGetConfig:
    """Tests for get_config dependency."""

    def test_returns_settings(self) -> None:
        result = get_config()
        assert isinstance(result, Settings)

    def test_returns_same_instance(self) -> None:
        a = get_config()
        b = get_config()
        assert a is b


class TestGetCurrentTenant:
    """Tests for get_current_tenant placeholder."""

    def test_returns_none(self) -> None:
        result = asyncio.run(get_current_tenant())
        assert result is None


class TestTypingAliases:
    """Tests for Annotated type aliases."""

    def test_db_session_type(self) -> None:
        hints = get_type_hints(self._db_func, include_extras=True)
        metadata = hints["db"].__metadata__
        assert any(isinstance(m, DependsClass) for m in metadata)

    def test_config_type(self) -> None:
        hints = get_type_hints(self._config_func, include_extras=True)
        metadata = hints["config"].__metadata__
        assert any(isinstance(m, DependsClass) for m in metadata)

    def test_tenant_id_type(self) -> None:
        hints = get_type_hints(self._tenant_func, include_extras=True)
        metadata = hints["tenant"].__metadata__
        assert any(isinstance(m, DependsClass) for m in metadata)

    @staticmethod
    def _db_func(db: DbSession) -> None:
        pass

    @staticmethod
    def _config_func(config: Config) -> None:
        pass

    @staticmethod
    def _tenant_func(tenant: TenantId) -> None:
        pass

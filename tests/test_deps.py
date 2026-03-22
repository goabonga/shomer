# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for FastAPI dependency injection helpers."""

import asyncio
import inspect
from typing import Annotated, get_type_hints

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
    """Tests for get_current_tenant from request state."""

    def test_returns_tenant_id_from_state(self) -> None:
        import uuid
        from unittest.mock import MagicMock

        tid = uuid.uuid4()
        req = MagicMock()
        req.state.tenant_id = tid
        result = asyncio.run(get_current_tenant(req))
        assert result == tid

    def test_returns_none_when_no_state(self) -> None:
        from unittest.mock import MagicMock

        req = MagicMock(spec=[])
        req.state = MagicMock(spec=[])
        result = asyncio.run(get_current_tenant(req))
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


class TestGetDbRollback:
    """Test get_db exception rollback path."""

    def test_rollback_on_commit_failure(self) -> None:
        """get_db rolls back when commit raises."""
        from unittest.mock import AsyncMock, patch

        async def _run() -> None:
            with patch("shomer.deps.async_session") as mock_factory:
                mock_session = AsyncMock()
                mock_cm = AsyncMock()
                mock_cm.__aenter__.return_value = mock_session
                mock_cm.__aexit__.return_value = False
                mock_factory.return_value = mock_cm
                mock_session.commit.side_effect = RuntimeError("db error")

                import pytest

                with pytest.raises(RuntimeError, match="db error"):
                    async for _s in get_db():
                        pass

                mock_session.rollback.assert_awaited_once()

        asyncio.run(_run())


class TestBearerTokenType:
    """Tests for BearerToken annotated type."""

    def test_bearer_token_is_annotated(self) -> None:
        from typing import get_args, get_origin

        from shomer.deps import BearerToken

        assert get_origin(BearerToken) is Annotated
        args = get_args(BearerToken)
        assert args[0] is str
        assert any(isinstance(a, DependsClass) for a in args[1:])

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for TenantMiddleware."""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import MagicMock

from shomer.deps import get_current_tenant


class TestGetCurrentTenant:
    """Tests for the get_current_tenant dependency."""

    def test_returns_tenant_id_from_state(self) -> None:
        async def _run() -> None:
            tid = uuid.uuid4()
            req = MagicMock()
            req.state.tenant_id = tid
            result = await get_current_tenant(req)
            assert result == tid

        asyncio.run(_run())

    def test_returns_none_when_no_state(self) -> None:
        async def _run() -> None:
            req = MagicMock(spec=[])
            req.state = MagicMock(spec=[])
            result = await get_current_tenant(req)
            assert result is None

        asyncio.run(_run())

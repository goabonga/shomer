# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for admin dashboard API route."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

from shomer.routes.admin_dashboard import dashboard


class TestDashboard:
    """Tests for GET /admin/dashboard."""

    @patch("shomer.routes.admin_dashboard.require_scope")
    def test_returns_all_statistics(self, _: MagicMock) -> None:
        """Returns aggregate statistics for all categories."""

        async def _run() -> None:
            # Mock results in order: total_users, active_users, verified_users,
            # active_sessions, total_clients, confidential_clients,
            # tokens_24h, mfa_enabled
            results = []
            for val in [100, 80, 75, 25, 10, 7, 500, 30]:
                r = MagicMock()
                r.scalar.return_value = val
                results.append(r)

            db = AsyncMock()
            db.execute.side_effect = results

            resp = await dashboard(db)
            data = json.loads(bytes(resp.body))

            assert data["users"]["total"] == 100
            assert data["users"]["active"] == 80
            assert data["users"]["verified"] == 75
            assert data["sessions"]["active"] == 25
            assert data["clients"]["total"] == 10
            assert data["clients"]["confidential"] == 7
            assert data["clients"]["public"] == 3
            assert data["tokens"]["issued_24h"] == 500
            assert data["mfa"]["enabled"] == 30
            assert data["mfa"]["adoption_rate"] == 30.0

        asyncio.run(_run())

    @patch("shomer.routes.admin_dashboard.require_scope")
    def test_zero_users_no_division_error(self, _: MagicMock) -> None:
        """Handles zero users without division by zero."""

        async def _run() -> None:
            results = []
            for val in [0, 0, 0, 0, 0, 0, 0, 0]:
                r = MagicMock()
                r.scalar.return_value = val
                results.append(r)

            db = AsyncMock()
            db.execute.side_effect = results

            resp = await dashboard(db)
            data = json.loads(bytes(resp.body))

            assert data["users"]["total"] == 0
            assert data["mfa"]["adoption_rate"] == 0.0

        asyncio.run(_run())

    @patch("shomer.routes.admin_dashboard.require_scope")
    def test_null_scalars_default_to_zero(self, _: MagicMock) -> None:
        """Handles None scalar results gracefully."""

        async def _run() -> None:
            results = []
            for _ in range(8):
                r = MagicMock()
                r.scalar.return_value = None
                results.append(r)

            db = AsyncMock()
            db.execute.side_effect = results

            resp = await dashboard(db)
            data = json.loads(bytes(resp.body))

            assert data["users"]["total"] == 0
            assert data["sessions"]["active"] == 0
            assert data["clients"]["total"] == 0
            assert data["tokens"]["issued_24h"] == 0

        asyncio.run(_run())

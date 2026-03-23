# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for admin UI dashboard route."""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from shomer.routes.admin_ui import admin_dashboard


def _req(cookies: dict[str, str] | None = None) -> MagicMock:
    """Create a mock Request with cookies."""
    cookie_data = cookies or {}
    r = MagicMock()
    r.cookies = MagicMock()
    r.cookies.get = lambda k, d=None: cookie_data.get(k, d)
    return r


class TestAdminDashboard:
    """Tests for GET /ui/admin."""

    @patch("shomer.routes.admin_ui._get_admin_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        """Unauthenticated users are redirected to login."""

        async def _run() -> None:
            mock_auth.return_value = None
            resp = await admin_dashboard(_req(), AsyncMock())
            assert resp.status_code == 302
            assert "/ui/login" in resp.headers["location"]

        asyncio.run(_run())

    @patch("shomer.routes.admin_ui._render")
    @patch("shomer.routes.admin_ui._get_admin_user")
    def test_authenticated_renders_dashboard(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Authenticated admin sees the dashboard with stats."""

        async def _run() -> None:
            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()
            mock_auth.return_value = mock_user
            mock_render.return_value = "html"

            # Mock 8 DB queries for stats
            results = []
            for val in [100, 80, 75, 25, 10, 7, 500, 30]:
                r = MagicMock()
                r.scalar.return_value = val
                results.append(r)

            db = AsyncMock()
            db.execute.side_effect = results

            await admin_dashboard(_req({"session_id": "tok"}), db)

            mock_render.assert_called_once()
            ctx = mock_render.call_args[0][2]
            assert ctx["section"] == "dashboard"
            assert ctx["stats"]["users"]["total"] == 100
            assert ctx["stats"]["sessions"]["active"] == 25
            assert ctx["stats"]["clients"]["total"] == 10
            assert ctx["stats"]["tokens"]["issued_24h"] == 500
            assert ctx["stats"]["mfa"]["adoption_rate"] == 30.0

        asyncio.run(_run())


class TestGetAdminUser:
    """Tests for _get_admin_user helper."""

    def test_no_cookie_returns_none(self) -> None:
        """Returns None when no session cookie."""

        async def _run() -> None:
            from shomer.routes.admin_ui import _get_admin_user

            result = await _get_admin_user(_req(), AsyncMock())
            assert result is None

        asyncio.run(_run())

    @patch("shomer.routes.admin_ui.SessionService")
    def test_invalid_session_returns_none(self, mock_cls: MagicMock) -> None:
        """Returns None for invalid session token."""

        async def _run() -> None:
            from shomer.routes.admin_ui import _get_admin_user

            mock_svc = AsyncMock()
            mock_svc.validate.return_value = None
            mock_cls.return_value = mock_svc

            result = await _get_admin_user(_req({"session_id": "bad"}), AsyncMock())
            assert result is None

        asyncio.run(_run())

    @patch("shomer.routes.admin_ui.RBACService")
    @patch("shomer.routes.admin_ui.SessionService")
    def test_non_admin_returns_none(
        self, mock_session_cls: MagicMock, mock_rbac_cls: MagicMock
    ) -> None:
        """Returns None for non-admin user."""

        async def _run() -> None:
            from shomer.routes.admin_ui import _get_admin_user

            mock_session = MagicMock(user_id=uuid.uuid4())
            mock_svc = AsyncMock()
            mock_svc.validate.return_value = mock_session
            mock_session_cls.return_value = mock_svc

            mock_user = MagicMock()
            mock_user.id = mock_session.user_id
            user_result = MagicMock()
            user_result.scalar_one_or_none.return_value = mock_user

            mock_rbac = AsyncMock()
            mock_rbac.has_permission.return_value = False
            mock_rbac_cls.return_value = mock_rbac

            db = AsyncMock()
            db.execute.return_value = user_result

            result = await _get_admin_user(_req({"session_id": "tok"}), db)
            assert result is None

        asyncio.run(_run())

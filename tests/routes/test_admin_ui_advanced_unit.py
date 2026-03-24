# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for admin UI advanced pages (sessions, JWKS, roles, PATs, tenants)."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from shomer.routes.admin_ui import (
    admin_jwks_list,
    admin_pats_list,
    admin_roles_list,
    admin_sessions_list,
    admin_tenants_list,
)


def _req(cookies: dict[str, str] | None = None) -> MagicMock:
    """Create a mock Request with cookies."""
    cookie_data = cookies or {}
    r = MagicMock()
    r.cookies = MagicMock()
    r.cookies.get = lambda k, d=None: cookie_data.get(k, d)
    return r


class TestAdminSessionsList:
    """Tests for GET /ui/admin/sessions."""

    @patch("shomer.routes.admin_ui._get_admin_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        """Non-admin redirects."""

        async def _run() -> None:
            mock_auth.return_value = None
            resp = await admin_sessions_list(_req(), AsyncMock())
            assert resp.status_code == 302
            assert "/ui/login" in resp.headers["location"]

        asyncio.run(_run())

    @patch("shomer.routes.admin_ui._render")
    @patch("shomer.routes.admin_ui._get_admin_user")
    def test_renders_sessions(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Renders empty sessions list."""

        async def _run() -> None:
            mock_auth.return_value = MagicMock()
            mock_render.return_value = "html"
            scalars = MagicMock()
            scalars.all.return_value = []
            result = MagicMock()
            result.scalars.return_value = scalars
            db = AsyncMock()
            db.execute.return_value = result

            await admin_sessions_list(_req({"session_id": "tok"}), db)
            ctx = mock_render.call_args[0][2]
            assert ctx["section"] == "sessions"
            assert ctx["sessions"] == []

        asyncio.run(_run())


class TestAdminJWKSList:
    """Tests for GET /ui/admin/jwks."""

    @patch("shomer.routes.admin_ui._get_admin_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        """Non-admin redirects."""

        async def _run() -> None:
            mock_auth.return_value = None
            resp = await admin_jwks_list(_req(), AsyncMock())
            assert resp.status_code == 302

        asyncio.run(_run())


class TestAdminRolesList:
    """Tests for GET /ui/admin/roles."""

    @patch("shomer.routes.admin_ui._get_admin_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        """Non-admin redirects."""

        async def _run() -> None:
            mock_auth.return_value = None
            resp = await admin_roles_list(_req(), AsyncMock())
            assert resp.status_code == 302

        asyncio.run(_run())


class TestAdminPATsList:
    """Tests for GET /ui/admin/pats."""

    @patch("shomer.routes.admin_ui._get_admin_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        """Non-admin redirects."""

        async def _run() -> None:
            mock_auth.return_value = None
            resp = await admin_pats_list(_req(), AsyncMock())
            assert resp.status_code == 302

        asyncio.run(_run())


class TestAdminTenantsList:
    """Tests for GET /ui/admin/tenants."""

    @patch("shomer.routes.admin_ui._get_admin_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        """Non-admin redirects."""

        async def _run() -> None:
            mock_auth.return_value = None
            resp = await admin_tenants_list(_req(), AsyncMock())
            assert resp.status_code == 302

        asyncio.run(_run())

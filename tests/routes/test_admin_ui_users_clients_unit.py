# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for admin UI users and clients pages."""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from shomer.routes.admin_ui import (
    admin_client_create_form,
    admin_client_detail,
    admin_clients_list,
    admin_user_create_form,
    admin_user_detail,
    admin_users_list,
)


def _req(cookies: dict[str, str] | None = None) -> MagicMock:
    """Create a mock Request with cookies."""
    cookie_data = cookies or {}
    r = MagicMock()
    r.cookies = MagicMock()
    r.cookies.get = lambda k, d=None: cookie_data.get(k, d)
    r.query_params = {}
    return r


class TestAdminUsersList:
    """Tests for GET /ui/admin/users."""

    @patch("shomer.routes.admin_ui._get_admin_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        """Non-admin redirects to login."""

        async def _run() -> None:
            mock_auth.return_value = None
            resp = await admin_users_list(_req(), AsyncMock())
            assert resp.status_code == 302
            assert "/ui/login" in resp.headers["location"]

        asyncio.run(_run())

    @patch("shomer.routes.admin_ui._render")
    @patch("shomer.routes.admin_ui._get_admin_user")
    def test_renders_users_list(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Renders users list page with items."""

        async def _run() -> None:
            mock_auth.return_value = MagicMock(id=uuid.uuid4())
            mock_render.return_value = "html"

            # count query
            count_r = MagicMock()
            count_r.scalar.return_value = 0
            # list query
            scalars = MagicMock()
            scalars.unique.return_value = scalars
            scalars.all.return_value = []
            list_r = MagicMock()
            list_r.scalars.return_value = scalars

            db = AsyncMock()
            db.execute.side_effect = [count_r, list_r]

            await admin_users_list(_req({"session_id": "tok"}), db)
            mock_render.assert_called_once()
            ctx = mock_render.call_args[0][2]
            assert ctx["section"] == "users"
            assert ctx["users"] == []

        asyncio.run(_run())


class TestAdminUserCreateForm:
    """Tests for GET /ui/admin/users/new."""

    @patch("shomer.routes.admin_ui._get_admin_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        """Non-admin redirects."""

        async def _run() -> None:
            mock_auth.return_value = None
            resp = await admin_user_create_form(_req(), AsyncMock())
            assert resp.status_code == 302

        asyncio.run(_run())

    @patch("shomer.routes.admin_ui._render")
    @patch("shomer.routes.admin_ui._get_admin_user")
    def test_renders_form(self, mock_auth: AsyncMock, mock_render: MagicMock) -> None:
        """Renders create form."""

        async def _run() -> None:
            mock_auth.return_value = MagicMock()
            mock_render.return_value = "html"
            await admin_user_create_form(_req({"session_id": "tok"}), AsyncMock())
            ctx = mock_render.call_args[0][2]
            assert ctx["edit"] is False

        asyncio.run(_run())


class TestAdminUserDetail:
    """Tests for GET /ui/admin/users/{id}."""

    @patch("shomer.routes.admin_ui._get_admin_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        """Non-admin redirects."""

        async def _run() -> None:
            mock_auth.return_value = None
            resp = await admin_user_detail(_req(), str(uuid.uuid4()), AsyncMock())
            assert resp.status_code == 302

        asyncio.run(_run())

    @patch("shomer.routes.admin_ui._get_admin_user")
    def test_invalid_uuid_redirects(self, mock_auth: AsyncMock) -> None:
        """Invalid UUID redirects to users list."""

        async def _run() -> None:
            mock_auth.return_value = MagicMock()
            resp = await admin_user_detail(
                _req({"session_id": "tok"}), "bad", AsyncMock()
            )
            assert resp.status_code == 302

        asyncio.run(_run())


class TestAdminClientsList:
    """Tests for GET /ui/admin/clients."""

    @patch("shomer.routes.admin_ui._get_admin_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        """Non-admin redirects."""

        async def _run() -> None:
            mock_auth.return_value = None
            resp = await admin_clients_list(_req(), AsyncMock())
            assert resp.status_code == 302

        asyncio.run(_run())

    @patch("shomer.routes.admin_ui._render")
    @patch("shomer.routes.admin_ui._get_admin_user")
    def test_renders_clients_list(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Renders empty clients list."""

        async def _run() -> None:
            mock_auth.return_value = MagicMock()
            mock_render.return_value = "html"

            scalars = MagicMock()
            scalars.all.return_value = []
            result = MagicMock()
            result.scalars.return_value = scalars
            db = AsyncMock()
            db.execute.return_value = result

            await admin_clients_list(_req({"session_id": "tok"}), db)
            ctx = mock_render.call_args[0][2]
            assert ctx["section"] == "clients"
            assert ctx["clients"] == []

        asyncio.run(_run())


class TestAdminClientCreateForm:
    """Tests for GET /ui/admin/clients/new."""

    @patch("shomer.routes.admin_ui._get_admin_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        """Non-admin redirects."""

        async def _run() -> None:
            mock_auth.return_value = None
            resp = await admin_client_create_form(_req(), AsyncMock())
            assert resp.status_code == 302

        asyncio.run(_run())


class TestAdminClientDetail:
    """Tests for GET /ui/admin/clients/{id}."""

    @patch("shomer.routes.admin_ui._get_admin_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        """Non-admin redirects."""

        async def _run() -> None:
            mock_auth.return_value = None
            resp = await admin_client_detail(_req(), str(uuid.uuid4()), AsyncMock())
            assert resp.status_code == 302

        asyncio.run(_run())

    @patch("shomer.routes.admin_ui._get_admin_user")
    def test_invalid_uuid_redirects(self, mock_auth: AsyncMock) -> None:
        """Invalid UUID redirects to clients list."""

        async def _run() -> None:
            mock_auth.return_value = MagicMock()
            resp = await admin_client_detail(
                _req({"session_id": "tok"}), "bad", AsyncMock()
            )
            assert resp.status_code == 302

        asyncio.run(_run())

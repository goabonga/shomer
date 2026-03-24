# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Pure unit tests for connected applications UI route handlers."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from shomer.routes.applications_ui import applications_page


class TestApplicationsPage:
    """Unit tests for GET /ui/settings/applications."""

    def test_unauthenticated_redirects(self) -> None:
        async def _run() -> None:
            with patch(
                "shomer.routes.applications_ui._get_session_user_id",
                new_callable=AsyncMock,
                return_value=None,
            ):
                req = MagicMock()
                resp = await applications_page(req, AsyncMock())
                assert resp.status_code == 302
                assert "/ui/login" in resp.headers["location"]

        asyncio.run(_run())

    def test_authenticated_renders_empty_list(self) -> None:
        async def _run() -> None:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_db.execute.return_value = mock_result

            with (
                patch(
                    "shomer.routes.applications_ui._get_session_user_id",
                    new_callable=AsyncMock,
                    return_value=uuid.uuid4(),
                ),
                patch("shomer.app.templates") as mock_tpl,
            ):
                mock_tpl.TemplateResponse.return_value = MagicMock()

                req = MagicMock()
                await applications_page(req, mock_db)
                mock_tpl.TemplateResponse.assert_called_once()
                call_args = mock_tpl.TemplateResponse.call_args
                ctx = call_args[0][2] if len(call_args[0]) > 2 else call_args[1]
                assert ctx["apps"] == []

        asyncio.run(_run())

    def test_authenticated_renders_apps(self) -> None:
        async def _run() -> None:
            now = datetime.now(timezone.utc)
            row = MagicMock()
            row.client_id = "app-1"
            row.client_name = "Test App"
            row.logo_uri = "https://example.com/logo.png"
            row.scopes = "openid profile"
            row.created_at = now

            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.all.return_value = [row]
            mock_db.execute.return_value = mock_result

            with (
                patch(
                    "shomer.routes.applications_ui._get_session_user_id",
                    new_callable=AsyncMock,
                    return_value=uuid.uuid4(),
                ),
                patch("shomer.app.templates") as mock_tpl,
            ):
                mock_tpl.TemplateResponse.return_value = MagicMock()

                req = MagicMock()
                await applications_page(req, mock_db)
                call_args = mock_tpl.TemplateResponse.call_args
                ctx = call_args[0][2] if len(call_args[0]) > 2 else call_args[1]
                assert len(ctx["apps"]) == 1
                assert ctx["apps"][0]["client_name"] == "Test App"
                assert "openid" in ctx["apps"][0]["scopes"]
                assert "profile" in ctx["apps"][0]["scopes"]

        asyncio.run(_run())

    def test_deduplicates_by_client_id(self) -> None:
        async def _run() -> None:
            now = datetime.now(timezone.utc)

            row1 = MagicMock()
            row1.client_id = "app-1"
            row1.client_name = "Test App"
            row1.logo_uri = None
            row1.scopes = "openid"
            row1.created_at = now

            row2 = MagicMock()
            row2.client_id = "app-1"
            row2.client_name = "Test App"
            row2.logo_uri = None
            row2.scopes = "profile email"
            row2.created_at = now

            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.all.return_value = [row1, row2]
            mock_db.execute.return_value = mock_result

            with (
                patch(
                    "shomer.routes.applications_ui._get_session_user_id",
                    new_callable=AsyncMock,
                    return_value=uuid.uuid4(),
                ),
                patch("shomer.app.templates") as mock_tpl,
            ):
                mock_tpl.TemplateResponse.return_value = MagicMock()

                req = MagicMock()
                await applications_page(req, mock_db)
                call_args = mock_tpl.TemplateResponse.call_args
                ctx = call_args[0][2] if len(call_args[0]) > 2 else call_args[1]
                assert len(ctx["apps"]) == 1
                scopes = ctx["apps"][0]["scopes"]
                assert "openid" in scopes
                assert "profile" in scopes
                assert "email" in scopes

        asyncio.run(_run())

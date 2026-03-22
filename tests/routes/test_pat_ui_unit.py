# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Pure unit tests for PAT UI route handlers."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from shomer.routes.pat_ui import pat_action, pat_list_page
from shomer.services.pat_service import PATCreateResult


class TestPATListPage:
    """Unit tests for GET /ui/settings/pats."""

    def test_unauthenticated_redirects(self) -> None:
        async def _run() -> None:
            with patch(
                "shomer.routes.pat_ui._get_session_user_id",
                new_callable=AsyncMock,
                return_value=None,
            ):
                req = MagicMock()
                resp = await pat_list_page(req, AsyncMock())
                assert resp.status_code == 302
                assert "/ui/login" in resp.headers["location"]

        asyncio.run(_run())

    def test_authenticated_renders_page(self) -> None:
        async def _run() -> None:
            with (
                patch(
                    "shomer.routes.pat_ui._get_session_user_id",
                    new_callable=AsyncMock,
                    return_value=uuid.uuid4(),
                ),
                patch("shomer.routes.pat_ui.PATService") as mock_cls,
                patch("shomer.app.templates") as mock_tpl,
            ):
                mock_svc = AsyncMock()
                mock_svc.list_for_user.return_value = []
                mock_cls.return_value = mock_svc
                mock_tpl.TemplateResponse.return_value = MagicMock()

                req = MagicMock()
                await pat_list_page(req, AsyncMock())
                mock_tpl.TemplateResponse.assert_called_once()
                call_args = mock_tpl.TemplateResponse.call_args
                ctx = call_args[0][2] if len(call_args[0]) > 2 else call_args[1]
                assert "tokens" in ctx

        asyncio.run(_run())


class TestPATAction:
    """Unit tests for POST /ui/settings/pats."""

    def test_unauthenticated_redirects(self) -> None:
        async def _run() -> None:
            with patch(
                "shomer.routes.pat_ui._get_session_user_id",
                new_callable=AsyncMock,
                return_value=None,
            ):
                req = MagicMock()
                resp = await pat_action(req, AsyncMock())
                assert resp.status_code == 302

        asyncio.run(_run())

    def test_create_returns_new_token(self) -> None:
        async def _run() -> None:
            now = datetime.now(timezone.utc)
            mock_result = PATCreateResult(
                id=uuid.uuid4(),
                name="test",
                token="shm_pat_secret123",
                token_prefix="shm_pat_secret1",
                scopes="api:read",
                expires_at=None,
                created_at=now,
            )

            with (
                patch(
                    "shomer.routes.pat_ui._get_session_user_id",
                    new_callable=AsyncMock,
                    return_value=uuid.uuid4(),
                ),
                patch("shomer.routes.pat_ui.PATService") as mock_cls,
                patch("shomer.app.templates") as mock_tpl,
            ):
                mock_svc = AsyncMock()
                mock_svc.create.return_value = mock_result
                mock_svc.list_for_user.return_value = []
                mock_cls.return_value = mock_svc
                mock_tpl.TemplateResponse.return_value = MagicMock()

                req = MagicMock()
                await pat_action(
                    req, AsyncMock(), action="create", name="test",
                    scopes="api:read", expires_at="", pat_id="",
                )
                call_args = mock_tpl.TemplateResponse.call_args
                ctx = call_args[0][2] if len(call_args[0]) > 2 else call_args[1]
                assert ctx["new_token"] == "shm_pat_secret123"
                assert ctx["success"] is not None

        asyncio.run(_run())

    def test_create_without_name_shows_error(self) -> None:
        async def _run() -> None:
            with (
                patch(
                    "shomer.routes.pat_ui._get_session_user_id",
                    new_callable=AsyncMock,
                    return_value=uuid.uuid4(),
                ),
                patch("shomer.routes.pat_ui.PATService") as mock_cls,
                patch("shomer.app.templates") as mock_tpl,
            ):
                mock_svc = AsyncMock()
                mock_svc.list_for_user.return_value = []
                mock_cls.return_value = mock_svc
                mock_tpl.TemplateResponse.return_value = MagicMock()

                req = MagicMock()
                await pat_action(
                    req, AsyncMock(), action="create", name="",
                    scopes="", expires_at="", pat_id="",
                )
                call_args = mock_tpl.TemplateResponse.call_args
                ctx = call_args[0][2] if len(call_args[0]) > 2 else call_args[1]
                assert "required" in ctx["error"].lower()

        asyncio.run(_run())

    def test_revoke_success(self) -> None:
        async def _run() -> None:
            with (
                patch(
                    "shomer.routes.pat_ui._get_session_user_id",
                    new_callable=AsyncMock,
                    return_value=uuid.uuid4(),
                ),
                patch("shomer.routes.pat_ui.PATService") as mock_cls,
                patch("shomer.app.templates") as mock_tpl,
            ):
                mock_svc = AsyncMock()
                mock_svc.list_for_user.return_value = []
                mock_cls.return_value = mock_svc
                mock_tpl.TemplateResponse.return_value = MagicMock()

                req = MagicMock()
                pid = str(uuid.uuid4())
                await pat_action(
                    req, AsyncMock(), action="revoke", pat_id=pid,
                    name="", scopes="", expires_at="",
                )
                mock_svc.revoke.assert_awaited_once()
                call_args = mock_tpl.TemplateResponse.call_args
                ctx = call_args[0][2] if len(call_args[0]) > 2 else call_args[1]
                assert "revoked" in ctx["success"].lower()

        asyncio.run(_run())

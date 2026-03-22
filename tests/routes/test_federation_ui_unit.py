# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for federation UI (login page with providers)."""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from shomer.routes.auth_ui import login_page


class TestLoginPageWithProviders:
    """Tests for login page federation provider rendering."""

    def test_login_page_without_tenant_no_providers(self) -> None:
        async def _run() -> None:
            with patch("shomer.app.templates") as mock_tpl:
                mock_tpl.TemplateResponse.return_value = MagicMock()
                req = MagicMock()
                req.state = MagicMock(spec=[])
                db = AsyncMock()

                await login_page(req, db)
                call_args = mock_tpl.TemplateResponse.call_args
                ctx = call_args[0][2] if len(call_args[0]) > 2 else call_args[1]
                assert ctx["federation_providers"] == []

        asyncio.run(_run())

    def test_login_page_with_tenant_fetches_providers(self) -> None:
        async def _run() -> None:
            mock_idp = MagicMock()
            mock_idp.id = uuid.uuid4()
            mock_idp.name = "Google"
            mock_idp.provider_type = MagicMock()
            mock_idp.provider_type.value = "google"
            mock_idp.icon_url = "https://icon.com/google.svg"
            mock_idp.button_text = "Sign in with Google"

            mock_slug_result = MagicMock()
            mock_slug_result.scalar_one_or_none.return_value = "acme"

            with (
                patch("shomer.app.templates") as mock_tpl,
                patch(
                    "shomer.services.federation_service.FederationService"
                ) as mock_fed_cls,
            ):
                mock_tpl.TemplateResponse.return_value = MagicMock()
                mock_fed = AsyncMock()
                mock_fed.get_tenant_identity_providers.return_value = [mock_idp]
                mock_fed_cls.return_value = mock_fed

                req = MagicMock()
                req.state.tenant_id = uuid.uuid4()
                db = AsyncMock()
                db.execute.return_value = mock_slug_result

                await login_page(req, db)
                call_args = mock_tpl.TemplateResponse.call_args
                ctx = call_args[0][2] if len(call_args[0]) > 2 else call_args[1]
                assert len(ctx["federation_providers"]) == 1
                assert ctx["federation_providers"][0]["name"] == "Google"
                assert (
                    ctx["federation_providers"][0]["button_text"]
                    == "Sign in with Google"
                )

        asyncio.run(_run())

    def test_login_page_with_error_params(self) -> None:
        async def _run() -> None:
            with patch("shomer.app.templates") as mock_tpl:
                mock_tpl.TemplateResponse.return_value = MagicMock()
                req = MagicMock()
                req.state = MagicMock(spec=[])
                db = AsyncMock()

                await login_page(
                    req,
                    db,
                    error="federation_failed",
                    message="User denied access",
                )
                call_args = mock_tpl.TemplateResponse.call_args
                ctx = call_args[0][2] if len(call_args[0]) > 2 else call_args[1]
                assert ctx["error"] == "User denied access"

        asyncio.run(_run())

    def test_login_page_button_text_fallback(self) -> None:
        async def _run() -> None:
            mock_idp = MagicMock()
            mock_idp.id = uuid.uuid4()
            mock_idp.name = "Acme SSO"
            mock_idp.provider_type = MagicMock()
            mock_idp.provider_type.value = "oidc"
            mock_idp.icon_url = None
            mock_idp.button_text = None

            mock_slug_result = MagicMock()
            mock_slug_result.scalar_one_or_none.return_value = "acme"

            with (
                patch("shomer.app.templates") as mock_tpl,
                patch(
                    "shomer.services.federation_service.FederationService"
                ) as mock_fed_cls,
            ):
                mock_tpl.TemplateResponse.return_value = MagicMock()
                mock_fed = AsyncMock()
                mock_fed.get_tenant_identity_providers.return_value = [mock_idp]
                mock_fed_cls.return_value = mock_fed

                req = MagicMock()
                req.state.tenant_id = uuid.uuid4()
                db = AsyncMock()
                db.execute.return_value = mock_slug_result

                await login_page(req, db)
                call_args = mock_tpl.TemplateResponse.call_args
                ctx = call_args[0][2] if len(call_args[0]) > 2 else call_args[1]
                assert (
                    ctx["federation_providers"][0]["button_text"]
                    == "Continue with Acme SSO"
                )

        asyncio.run(_run())

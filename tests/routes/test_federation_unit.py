# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Pure unit tests for federation route handlers."""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from shomer.routes.federation import initiate_federation, list_providers


class TestListProviders:
    """Unit tests for GET /federation/providers."""

    def test_no_tenant_returns_400(self) -> None:
        async def _run() -> None:
            req = MagicMock()
            req.state = MagicMock(spec=[])
            db = AsyncMock()
            with pytest.raises(HTTPException) as exc_info:
                await list_providers(db, req, tenant_slug=None)
            assert exc_info.value.status_code == 400

        asyncio.run(_run())

    def test_with_tenant_slug_returns_providers(self) -> None:
        async def _run() -> None:
            idp = MagicMock()
            idp.id = uuid.uuid4()
            idp.name = "Google"
            idp.provider_type = MagicMock()
            idp.provider_type.value = "google"
            idp.icon_url = "https://icon.com/google.svg"
            idp.button_text = None

            with patch("shomer.routes.federation.FederationService") as mock_cls:
                mock_svc = AsyncMock()
                mock_svc.get_tenant_identity_providers.return_value = [idp]
                mock_cls.return_value = mock_svc

                req = MagicMock()
                db = AsyncMock()
                resp = await list_providers(db, req, tenant_slug="acme")

            import json

            body = json.loads(bytes(resp.body))
            assert body["tenant_slug"] == "acme"
            assert len(body["providers"]) == 1
            assert body["providers"][0]["name"] == "Google"
            assert body["providers"][0]["button_text"] == "Continue with Google"
            assert body["local_login_enabled"] is True

        asyncio.run(_run())


class TestInitiateFederation:
    """Unit tests for GET /federation/{idp_id}/authorize."""

    def test_no_tenant_context_returns_400(self) -> None:
        async def _run() -> None:
            req = MagicMock()
            req.state = MagicMock(spec=[])
            db = AsyncMock()
            with pytest.raises(HTTPException) as exc_info:
                await initiate_federation(req, "idp-1", db)
            assert exc_info.value.status_code == 400

        asyncio.run(_run())

    def test_idp_not_found_returns_404(self) -> None:
        async def _run() -> None:
            mock_slug_result = MagicMock()
            mock_slug_result.scalar_one_or_none.return_value = "acme"

            with patch("shomer.routes.federation.FederationService") as mock_cls:
                mock_svc = AsyncMock()
                mock_svc.get_identity_provider.return_value = None
                mock_cls.return_value = mock_svc

                req = MagicMock()
                req.state.tenant_id = uuid.uuid4()
                db = AsyncMock()
                db.execute.return_value = mock_slug_result

                with pytest.raises(HTTPException) as exc_info:
                    await initiate_federation(req, "unknown", db)
                assert exc_info.value.status_code == 404

        asyncio.run(_run())

    def test_inactive_idp_returns_400(self) -> None:
        async def _run() -> None:
            mock_slug_result = MagicMock()
            mock_slug_result.scalar_one_or_none.return_value = "acme"

            idp = MagicMock()
            idp.is_active = False

            with patch("shomer.routes.federation.FederationService") as mock_cls:
                mock_svc = AsyncMock()
                mock_svc.get_identity_provider.return_value = idp
                mock_cls.return_value = mock_svc

                req = MagicMock()
                req.state.tenant_id = uuid.uuid4()
                db = AsyncMock()
                db.execute.return_value = mock_slug_result

                with pytest.raises(HTTPException) as exc_info:
                    await initiate_federation(req, "idp-1", db)
                assert exc_info.value.status_code == 400

        asyncio.run(_run())

    def test_success_redirects(self) -> None:
        async def _run() -> None:
            mock_slug_result = MagicMock()
            mock_slug_result.scalar_one_or_none.return_value = "acme"

            idp = MagicMock()
            idp.id = uuid.uuid4()
            idp.is_active = True

            with patch("shomer.routes.federation.FederationService") as mock_cls:
                mock_svc = AsyncMock()
                mock_svc.get_identity_provider.return_value = idp
                mock_svc.get_authorization_url.return_value = (
                    "https://idp.example.com/authorize?client_id=test"
                )
                mock_cls.return_value = mock_svc
                mock_cls.generate_nonce.return_value = "nonce"
                mock_cls.generate_code_verifier.return_value = "verifier"
                mock_cls.generate_state.return_value = "state"

                req = MagicMock()
                req.state.tenant_id = uuid.uuid4()
                req.headers = MagicMock()
                req.headers.get = MagicMock(side_effect=lambda k, d="": d)
                req.url = MagicMock()
                req.url.scheme = "https"
                req.url.netloc = "acme.shomer.io"
                db = AsyncMock()
                db.execute.return_value = mock_slug_result

                resp = await initiate_federation(
                    req, str(idp.id), db,
                    redirect_uri=None, state=None,
                )
                assert resp.status_code == 302

        asyncio.run(_run())

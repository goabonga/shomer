# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for TenantBrandingService."""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

from shomer.services.tenant_branding_service import (
    DEFAULT_BRANDING,
    BrandingContext,
    TenantBrandingService,
)


class TestGetBranding:
    """Tests for branding resolution."""

    def test_none_tenant_returns_default(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            svc = TenantBrandingService(db)
            result = await svc.get_branding(None)
            assert result is DEFAULT_BRANDING

        asyncio.run(_run())

    def test_no_branding_record_returns_default(self) -> None:
        async def _run() -> None:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TenantBrandingService(db)
            result = await svc.get_branding(uuid.uuid4())
            assert result is DEFAULT_BRANDING

        asyncio.run(_run())

    def test_branding_record_returns_custom(self) -> None:
        async def _run() -> None:
            mock_branding = MagicMock()
            mock_branding.logo_url = "https://acme.com/logo.png"
            mock_branding.favicon_url = "https://acme.com/fav.ico"
            mock_branding.primary_color = "#ff0000"
            mock_branding.secondary_color = "#00ff00"
            mock_branding.custom_css = "h1 { color: red; }"

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_branding

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TenantBrandingService(db)
            result = await svc.get_branding(uuid.uuid4())
            assert isinstance(result, BrandingContext)
            assert result.logo_url == "https://acme.com/logo.png"
            assert result.primary_color == "#ff0000"
            assert result.custom_css == "h1 { color: red; }"

        asyncio.run(_run())

    def test_null_colors_use_defaults(self) -> None:
        async def _run() -> None:
            mock_branding = MagicMock()
            mock_branding.logo_url = None
            mock_branding.favicon_url = None
            mock_branding.primary_color = None
            mock_branding.secondary_color = None
            mock_branding.custom_css = None

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_branding

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TenantBrandingService(db)
            result = await svc.get_branding(uuid.uuid4())
            assert result.primary_color == "#333333"
            assert result.secondary_color == "#666666"
            assert result.custom_css == ""

        asyncio.run(_run())


class TestGetTemplate:
    """Tests for custom template resolution."""

    def test_none_tenant_returns_none(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            svc = TenantBrandingService(db)
            result = await svc.get_template(None, "login")
            assert result is None

        asyncio.run(_run())

    def test_no_custom_template_returns_none(self) -> None:
        async def _run() -> None:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TenantBrandingService(db)
            result = await svc.get_template(uuid.uuid4(), "login")
            assert result is None

        asyncio.run(_run())

    def test_custom_template_returned(self) -> None:
        async def _run() -> None:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = "<h1>Custom</h1>"

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TenantBrandingService(db)
            result = await svc.get_template(uuid.uuid4(), "login")
            assert result == "<h1>Custom</h1>"

        asyncio.run(_run())


class TestGetBrandingDict:
    """Tests for branding dict for template context."""

    def test_returns_dict_with_branding_keys(self) -> None:
        async def _run() -> None:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TenantBrandingService(db)
            d = await svc.get_branding_dict(uuid.uuid4())
            assert "branding_logo_url" in d
            assert "branding_primary_color" in d
            assert "branding_custom_css" in d
            assert d["branding_primary_color"] == "#333333"

        asyncio.run(_run())

    def test_none_tenant_returns_defaults(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            svc = TenantBrandingService(db)
            d = await svc.get_branding_dict(None)
            assert d["branding_logo_url"] is None
            assert d["branding_primary_color"] == "#333333"

        asyncio.run(_run())

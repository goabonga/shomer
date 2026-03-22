# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for TenantBrandingService."""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

from shomer.services.tenant_branding_service import (
    CUSTOMIZABLE_TEMPLATES,
    DEFAULT_BRANDING,
    BrandingContext,
    TenantBrandingService,
)


class TestBrandingContext:
    """Tests for BrandingContext dataclass."""

    def test_defaults(self) -> None:
        ctx = BrandingContext()
        assert ctx.primary_color == "#e94560"
        assert ctx.show_powered_by is True
        assert ctx.custom_css == ""
        assert ctx.custom_js == ""

    def test_css_variables(self) -> None:
        ctx = BrandingContext()
        css = ctx.to_css_variables()
        assert "--primary-color: #e94560" in css
        assert "--text-color: #e0e0e0" in css
        assert ":root {" in css

    def test_font_import_with_url(self) -> None:
        ctx = BrandingContext(font_url="https://fonts.googleapis.com/css2?family=Inter")
        assert (
            '@import url("https://fonts.googleapis.com/css2?family=Inter")'
            in ctx.get_font_import()
        )

    def test_font_import_without_url(self) -> None:
        ctx = BrandingContext()
        assert ctx.get_font_import() == ""


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
            mock_branding.logo_dark_url = "https://acme.com/logo-dark.png"
            mock_branding.favicon_url = "https://acme.com/fav.ico"
            mock_branding.primary_color = "#ff0000"
            mock_branding.secondary_color = "#00ff00"
            mock_branding.accent_color = "#0000ff"
            mock_branding.background_color = "#111111"
            mock_branding.surface_color = "#222222"
            mock_branding.text_color = "#ffffff"
            mock_branding.text_muted_color = "#cccccc"
            mock_branding.error_color = "#ff0000"
            mock_branding.success_color = "#00ff00"
            mock_branding.border_color = "#333333"
            mock_branding.warning_color = "#ffff00"
            mock_branding.info_color = "#00ffff"
            mock_branding.font_family = "'Inter', sans-serif"
            mock_branding.font_url = "https://fonts.example.com"
            mock_branding.custom_css = "h1 { color: red; }"
            mock_branding.custom_js = "console.log('hi');"
            mock_branding.show_powered_by = False

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_branding

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TenantBrandingService(db)
            result = await svc.get_branding(uuid.uuid4())
            assert isinstance(result, BrandingContext)
            assert result.logo_url == "https://acme.com/logo.png"
            assert result.logo_dark_url == "https://acme.com/logo-dark.png"
            assert result.primary_color == "#ff0000"
            assert result.accent_color == "#0000ff"
            assert result.font_family == "'Inter', sans-serif"
            assert result.custom_js == "console.log('hi');"
            assert result.show_powered_by is False

        asyncio.run(_run())

    def test_null_colors_use_defaults(self) -> None:
        async def _run() -> None:
            mock_branding = MagicMock()
            for attr in [
                "logo_url",
                "logo_dark_url",
                "favicon_url",
                "primary_color",
                "secondary_color",
                "accent_color",
                "background_color",
                "surface_color",
                "text_color",
                "text_muted_color",
                "error_color",
                "success_color",
                "border_color",
                "warning_color",
                "info_color",
                "font_family",
                "font_url",
                "custom_css",
                "custom_js",
            ]:
                setattr(mock_branding, attr, None)
            mock_branding.show_powered_by = True

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_branding

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TenantBrandingService(db)
            result = await svc.get_branding(uuid.uuid4())
            assert result.primary_color == DEFAULT_BRANDING.primary_color
            assert result.text_color == DEFAULT_BRANDING.text_color
            assert result.custom_css == ""

        asyncio.run(_run())


class TestGetBrandingDict:
    """Tests for branding dict for template context."""

    def test_includes_css_variables(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            svc = TenantBrandingService(db)
            d = await svc.get_branding_dict(None)
            assert "branding" in d
            assert "branding_css_variables" in d
            assert "branding_font_import" in d
            assert "--primary-color" in str(d["branding_css_variables"])

        asyncio.run(_run())


class TestGetTemplate:
    """Tests for custom template resolution."""

    def test_none_tenant_returns_none(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            svc = TenantBrandingService(db)
            result = await svc.get_template(None, "auth/login.html")
            assert result is None

        asyncio.run(_run())

    def test_no_custom_template_returns_none(self) -> None:
        async def _run() -> None:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TenantBrandingService(db)
            result = await svc.get_template(uuid.uuid4(), "auth/login.html")
            assert result is None

        asyncio.run(_run())

    def test_custom_template_returned(self) -> None:
        async def _run() -> None:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = "<h1>Custom</h1>"

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TenantBrandingService(db)
            result = await svc.get_template(uuid.uuid4(), "auth/login.html")
            assert result == "<h1>Custom</h1>"

        asyncio.run(_run())


class TestBrandingCRUD:
    """Tests for save/delete branding."""

    def test_save_branding_creates_new(self) -> None:
        async def _run() -> None:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TenantBrandingService(db)
            await svc.save_branding(uuid.uuid4(), primary_color="#ff0000")
            db.add.assert_called_once()

        asyncio.run(_run())

    def test_save_branding_updates_existing(self) -> None:
        async def _run() -> None:
            existing = MagicMock()
            existing.primary_color = "#000000"
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = existing

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TenantBrandingService(db)
            await svc.save_branding(uuid.uuid4(), primary_color="#ff0000")
            assert existing.primary_color == "#ff0000"

        asyncio.run(_run())

    def test_delete_branding_returns_true(self) -> None:
        async def _run() -> None:
            existing = MagicMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = existing

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TenantBrandingService(db)
            result = await svc.delete_branding(uuid.uuid4())
            assert result is True
            db.delete.assert_awaited_once()

        asyncio.run(_run())

    def test_delete_branding_not_found(self) -> None:
        async def _run() -> None:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TenantBrandingService(db)
            result = await svc.delete_branding(uuid.uuid4())
            assert result is False

        asyncio.run(_run())


class TestTemplateCRUD:
    """Tests for save/delete/list templates."""

    def test_save_template_creates_new(self) -> None:
        async def _run() -> None:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TenantBrandingService(db)
            await svc.save_template(uuid.uuid4(), "auth/login.html", "<h1>Custom</h1>")
            db.add.assert_called_once()

        asyncio.run(_run())

    def test_save_template_updates_existing(self) -> None:
        async def _run() -> None:
            existing = MagicMock()
            existing.content = "<h1>Old</h1>"
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = existing

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TenantBrandingService(db)
            await svc.save_template(
                uuid.uuid4(),
                "auth/login.html",
                "<h1>New</h1>",
                description="Updated",
                is_active=False,
            )
            assert existing.content == "<h1>New</h1>"
            assert existing.description == "Updated"
            assert existing.is_active is False

        asyncio.run(_run())

    def test_delete_template_returns_true(self) -> None:
        async def _run() -> None:
            existing = MagicMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = existing

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TenantBrandingService(db)
            result = await svc.delete_template(uuid.uuid4(), "auth/login.html")
            assert result is True

        asyncio.run(_run())

    def test_delete_template_not_found(self) -> None:
        async def _run() -> None:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TenantBrandingService(db)
            result = await svc.delete_template(uuid.uuid4(), "auth/login.html")
            assert result is False

        asyncio.run(_run())

    def test_list_templates(self) -> None:
        async def _run() -> None:
            t1 = MagicMock()
            t2 = MagicMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [t1, t2]

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TenantBrandingService(db)
            result = await svc.list_templates(uuid.uuid4())
            assert len(result) == 2

        asyncio.run(_run())


class TestCustomizableTemplates:
    """Tests for the CUSTOMIZABLE_TEMPLATES list."""

    def test_includes_auth_templates(self) -> None:
        assert "auth/login.html" in CUSTOMIZABLE_TEMPLATES
        assert "auth/register.html" in CUSTOMIZABLE_TEMPLATES

    def test_includes_oauth2_templates(self) -> None:
        assert "oauth2/consent.html" in CUSTOMIZABLE_TEMPLATES
        assert "oauth2/error.html" in CUSTOMIZABLE_TEMPLATES

    def test_includes_email_templates(self) -> None:
        assert "email/verification.html" in CUSTOMIZABLE_TEMPLATES
        assert "email/password_reset.html" in CUSTOMIZABLE_TEMPLATES

    def test_includes_mfa_templates(self) -> None:
        assert "mfa/setup.html" in CUSTOMIZABLE_TEMPLATES
        assert "mfa/challenge.html" in CUSTOMIZABLE_TEMPLATES

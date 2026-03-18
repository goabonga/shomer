# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for CORS middleware configuration."""

from fastapi import FastAPI

from shomer.core.settings import Settings
from shomer.middleware.cors import DEV_ORIGINS, resolve_origins, setup_cors


class TestResolveOrigins:
    """Tests for resolve_origins()."""

    def test_empty_by_default(self) -> None:
        settings = Settings(cors_allowed_origins=[])
        assert resolve_origins(settings) == []

    def test_configured_origins(self) -> None:
        origins = ["https://app.example.com", "https://other.example.com"]
        settings = Settings(cors_allowed_origins=origins)
        assert resolve_origins(settings) == origins

    def test_debug_adds_dev_origins(self) -> None:
        settings = Settings(debug=True, cors_allowed_origins=[])
        result = resolve_origins(settings)
        for origin in DEV_ORIGINS:
            assert origin in result

    def test_debug_with_configured_origins(self) -> None:
        settings = Settings(
            debug=True,
            cors_allowed_origins=["https://app.example.com"],
        )
        result = resolve_origins(settings)
        assert result[0] == "https://app.example.com"
        assert "http://localhost:3000" in result

    def test_tenant_origins_merged(self) -> None:
        settings = Settings(
            cors_allowed_origins=["https://main.example.com"],
        )
        tenant = ["https://tenant1.example.com"]
        result = resolve_origins(settings, tenant_origins=tenant)
        assert "https://main.example.com" in result
        assert "https://tenant1.example.com" in result

    def test_deduplicates_origins(self) -> None:
        settings = Settings(
            cors_allowed_origins=["https://a.com", "https://a.com"],
        )
        result = resolve_origins(settings)
        assert result == ["https://a.com"]

    def test_tenant_none_ignored(self) -> None:
        settings = Settings(cors_allowed_origins=["https://a.com"])
        result = resolve_origins(settings, tenant_origins=None)
        assert result == ["https://a.com"]

    def test_no_debug_no_dev_origins(self) -> None:
        settings = Settings(debug=False, cors_allowed_origins=[])
        result = resolve_origins(settings)
        assert all(o not in result for o in DEV_ORIGINS)


class TestSetupCors:
    """Tests for setup_cors()."""

    def test_adds_cors_middleware(self) -> None:
        app = FastAPI()
        settings = Settings(
            cors_allowed_origins=["https://example.com"],
        )
        setup_cors(app, settings)
        assert len(app.user_middleware) == 1
        cls = getattr(app.user_middleware[0], "cls", None)
        assert cls is not None
        assert cls.__name__ == "CORSMiddleware"

    def test_credentials_enabled_by_default(self) -> None:
        settings = Settings()
        assert settings.cors_allow_credentials is True

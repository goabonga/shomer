# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for IssuerResolver."""

from __future__ import annotations

import uuid
from unittest.mock import patch

from shomer.core.settings import Settings
from shomer.services.issuer_resolver import IssuerResolver

_ISSUER = "https://auth.shomer.local"


def _settings(**overrides: str) -> Settings:
    defaults: dict[str, str] = {"jwt_issuer": _ISSUER}
    defaults.update(overrides)
    return Settings(**defaults)  # type: ignore[arg-type]


class TestResolve:
    """Tests for IssuerResolver.resolve()."""

    def test_default_issuer_when_no_tenant(self) -> None:
        resolver = IssuerResolver(_settings())
        assert resolver.resolve() == _ISSUER

    def test_default_issuer_when_tenant_has_no_custom(self) -> None:
        resolver = IssuerResolver(_settings())
        assert resolver.resolve(uuid.uuid4()) == _ISSUER

    def test_tenant_specific_issuer(self) -> None:
        resolver = IssuerResolver(_settings())
        tenant_id = uuid.uuid4()
        with patch.object(
            IssuerResolver,
            "_lookup_tenant_issuer",
            return_value="https://tenant1.auth.example.com",
        ):
            assert resolver.resolve(tenant_id) == "https://tenant1.auth.example.com"

    def test_custom_default_issuer(self) -> None:
        resolver = IssuerResolver(_settings(jwt_issuer="https://custom.example.com"))
        assert resolver.resolve() == "https://custom.example.com"


class TestEndpoints:
    """Tests for endpoint URL builders."""

    def test_token_endpoint(self) -> None:
        resolver = IssuerResolver(_settings())
        assert resolver.get_token_endpoint() == f"{_ISSUER}/auth/token"

    def test_authorization_endpoint(self) -> None:
        resolver = IssuerResolver(_settings())
        assert resolver.get_authorization_endpoint() == f"{_ISSUER}/auth/authorize"

    def test_jwks_uri(self) -> None:
        resolver = IssuerResolver(_settings())
        assert resolver.get_jwks_uri() == f"{_ISSUER}/.well-known/jwks.json"

    def test_userinfo_endpoint(self) -> None:
        resolver = IssuerResolver(_settings())
        assert resolver.get_userinfo_endpoint() == f"{_ISSUER}/userinfo"

    def test_endpoints_with_tenant(self) -> None:
        resolver = IssuerResolver(_settings())
        tenant_id = uuid.uuid4()
        with patch.object(
            IssuerResolver,
            "_lookup_tenant_issuer",
            return_value="https://t1.example.com",
        ):
            assert (
                resolver.get_token_endpoint(tenant_id)
                == "https://t1.example.com/auth/token"
            )
            assert (
                resolver.get_jwks_uri(tenant_id)
                == "https://t1.example.com/.well-known/jwks.json"
            )


class TestLookupPlaceholder:
    """Tests for the placeholder tenant lookup."""

    def test_placeholder_returns_none(self) -> None:
        assert IssuerResolver._lookup_tenant_issuer(uuid.uuid4()) is None

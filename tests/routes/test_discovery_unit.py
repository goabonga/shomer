# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for OIDC Discovery endpoint."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import MagicMock, patch

from shomer.routes.discovery import DISCOVERY_CACHE_MAX_AGE, openid_configuration


class TestOpenIDConfiguration:
    """Tests for GET /.well-known/openid-configuration."""

    @patch("shomer.routes.discovery.get_settings")
    def test_returns_issuer(self, mock_settings: MagicMock) -> None:
        settings = MagicMock()
        settings.jwt_issuer = "https://auth.shomer.local"
        mock_settings.return_value = settings

        async def _run() -> None:
            resp = await openid_configuration()
            body = json.loads(bytes(resp.body))
            assert body["issuer"] == "https://auth.shomer.local"

        asyncio.run(_run())

    @patch("shomer.routes.discovery.get_settings")
    def test_contains_required_endpoints(self, mock_settings: MagicMock) -> None:
        settings = MagicMock()
        settings.jwt_issuer = "https://auth.example.com"
        mock_settings.return_value = settings

        async def _run() -> None:
            resp = await openid_configuration()
            body = json.loads(bytes(resp.body))
            assert (
                body["authorization_endpoint"]
                == "https://auth.example.com/oauth2/authorize"
            )
            assert body["token_endpoint"] == "https://auth.example.com/oauth2/token"
            assert body["userinfo_endpoint"] == "https://auth.example.com/userinfo"
            assert body["jwks_uri"] == "https://auth.example.com/.well-known/jwks.json"

        asyncio.run(_run())

    @patch("shomer.routes.discovery.get_settings")
    def test_scopes_supported(self, mock_settings: MagicMock) -> None:
        mock_settings.return_value = MagicMock(jwt_issuer="https://x")

        async def _run() -> None:
            resp = await openid_configuration()
            body = json.loads(bytes(resp.body))
            assert "openid" in body["scopes_supported"]
            assert "profile" in body["scopes_supported"]
            assert "email" in body["scopes_supported"]

        asyncio.run(_run())

    @patch("shomer.routes.discovery.get_settings")
    def test_grant_types_supported(self, mock_settings: MagicMock) -> None:
        mock_settings.return_value = MagicMock(jwt_issuer="https://x")

        async def _run() -> None:
            resp = await openid_configuration()
            body = json.loads(bytes(resp.body))
            grants = body["grant_types_supported"]
            assert "authorization_code" in grants
            assert "client_credentials" in grants
            assert "password" in grants
            assert "refresh_token" in grants

        asyncio.run(_run())

    @patch("shomer.routes.discovery.get_settings")
    def test_response_types_supported(self, mock_settings: MagicMock) -> None:
        mock_settings.return_value = MagicMock(jwt_issuer="https://x")

        async def _run() -> None:
            resp = await openid_configuration()
            body = json.loads(bytes(resp.body))
            assert "code" in body["response_types_supported"]

        asyncio.run(_run())

    @patch("shomer.routes.discovery.get_settings")
    def test_token_endpoint_auth_methods(self, mock_settings: MagicMock) -> None:
        mock_settings.return_value = MagicMock(jwt_issuer="https://x")

        async def _run() -> None:
            resp = await openid_configuration()
            body = json.loads(bytes(resp.body))
            methods = body["token_endpoint_auth_methods_supported"]
            assert "client_secret_basic" in methods
            assert "client_secret_post" in methods
            assert "none" in methods

        asyncio.run(_run())

    @patch("shomer.routes.discovery.get_settings")
    def test_code_challenge_methods(self, mock_settings: MagicMock) -> None:
        mock_settings.return_value = MagicMock(jwt_issuer="https://x")

        async def _run() -> None:
            resp = await openid_configuration()
            body = json.loads(bytes(resp.body))
            assert "S256" in body["code_challenge_methods_supported"]

        asyncio.run(_run())

    @patch("shomer.routes.discovery.get_settings")
    def test_claims_supported(self, mock_settings: MagicMock) -> None:
        mock_settings.return_value = MagicMock(jwt_issuer="https://x")

        async def _run() -> None:
            resp = await openid_configuration()
            body = json.loads(bytes(resp.body))
            claims = body["claims_supported"]
            for claim in ["sub", "iss", "email", "name", "address"]:
                assert claim in claims

        asyncio.run(_run())

    @patch("shomer.routes.discovery.get_settings")
    def test_cache_control_header(self, mock_settings: MagicMock) -> None:
        mock_settings.return_value = MagicMock(jwt_issuer="https://x")

        async def _run() -> None:
            resp = await openid_configuration()
            cc = resp.headers.get("cache-control", "")
            assert f"max-age={DISCOVERY_CACHE_MAX_AGE}" in cc

        asyncio.run(_run())

    @patch("shomer.routes.discovery.get_settings")
    def test_additional_endpoints(self, mock_settings: MagicMock) -> None:
        settings = MagicMock()
        settings.jwt_issuer = "https://auth.example.com"
        mock_settings.return_value = settings

        async def _run() -> None:
            resp = await openid_configuration()
            body = json.loads(bytes(resp.body))
            assert (
                body["revocation_endpoint"] == "https://auth.example.com/oauth2/revoke"
            )
            assert (
                body["introspection_endpoint"]
                == "https://auth.example.com/oauth2/introspect"
            )
            assert (
                body["end_session_endpoint"] == "https://auth.example.com/auth/logout"
            )

        asyncio.run(_run())

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for admin JWKS API routes."""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from shomer.routes.admin_jwks import get_key, list_keys, revoke_key, rotate_key


def _mock_jwk(
    kid: str = "shomer-abc123",
    algorithm: str = "RS256",
    status_val: str = "active",
) -> MagicMock:
    """Create a mock JWK."""
    k = MagicMock()
    k.id = uuid.uuid4()
    k.kid = kid
    k.algorithm = algorithm
    k.status = MagicMock(value=status_val)
    k.public_key = json.dumps(
        {"kty": "RSA", "kid": kid, "alg": algorithm, "use": "sig"}
    )
    k.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return k


class TestListKeys:
    """Tests for GET /admin/jwks."""

    @patch("shomer.routes.admin_jwks.require_scope")
    def test_returns_all_keys(self, _mock_rbac: MagicMock) -> None:
        """Returns all keys with status."""

        async def _run() -> None:
            k1 = _mock_jwk(kid="k1", status_val="active")
            k2 = _mock_jwk(kid="k2", status_val="rotated")

            scalars_mock = MagicMock()
            scalars_mock.all.return_value = [k1, k2]
            result = MagicMock()
            result.scalars.return_value = scalars_mock

            db = AsyncMock()
            db.execute.return_value = result

            resp = await list_keys(db)
            data = json.loads(bytes(resp.body))
            assert data["total"] == 2
            assert data["keys"][0]["kid"] == "k1"
            assert data["keys"][0]["status"] == "active"
            assert data["keys"][1]["status"] == "rotated"

        asyncio.run(_run())

    @patch("shomer.routes.admin_jwks.require_scope")
    def test_empty_list(self, _mock_rbac: MagicMock) -> None:
        """Returns empty list when no keys."""

        async def _run() -> None:
            scalars_mock = MagicMock()
            scalars_mock.all.return_value = []
            result = MagicMock()
            result.scalars.return_value = scalars_mock

            db = AsyncMock()
            db.execute.return_value = result

            resp = await list_keys(db)
            data = json.loads(bytes(resp.body))
            assert data["total"] == 0
            assert data["keys"] == []

        asyncio.run(_run())


class TestGetKey:
    """Tests for GET /admin/jwks/{kid}."""

    @patch("shomer.routes.admin_jwks.require_scope")
    def test_returns_key_detail(self, _mock_rbac: MagicMock) -> None:
        """Returns key details with public key."""

        async def _run() -> None:
            mock = _mock_jwk()
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock

            db = AsyncMock()
            db.execute.return_value = result

            resp = await get_key("shomer-abc123", db)
            data = json.loads(bytes(resp.body))
            assert data["kid"] == "shomer-abc123"
            assert data["algorithm"] == "RS256"
            assert data["public_key"]["kty"] == "RSA"

        asyncio.run(_run())

    @patch("shomer.routes.admin_jwks.require_scope")
    def test_not_found_returns_404(self, _mock_rbac: MagicMock) -> None:
        """Returns 404 when key not found."""

        async def _run() -> None:
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db = AsyncMock()
            db.execute.return_value = result

            try:
                await get_key("nonexistent", db)
                raise AssertionError("Expected HTTPException")
            except HTTPException as exc:
                assert exc.status_code == 404

        asyncio.run(_run())


class TestRotateKey:
    """Tests for POST /admin/jwks/rotate."""

    @patch("shomer.routes.admin_jwks.require_scope")
    @patch("shomer.core.settings.get_settings")
    @patch("shomer.core.security.AESEncryption")
    @patch("shomer.services.jwk_service.JWKService")
    def test_rotates_and_returns_new_key(
        self,
        mock_svc_cls: MagicMock,
        _mock_aes: MagicMock,
        _mock_settings: MagicMock,
        _mock_rbac: MagicMock,
    ) -> None:
        """Generates a new key and returns it."""

        async def _run() -> None:
            new_key = _mock_jwk(kid="shomer-new123")
            mock_svc = AsyncMock()
            mock_svc.rotate.return_value = new_key
            mock_svc_cls.return_value = mock_svc

            db = AsyncMock()
            resp = await rotate_key(db)
            data = json.loads(bytes(resp.body))
            assert data["kid"] == "shomer-new123"
            assert data["message"] == "Key rotated successfully"

        asyncio.run(_run())


class TestRevokeKey:
    """Tests for DELETE /admin/jwks/{kid}."""

    @patch("shomer.routes.admin_jwks.require_scope")
    @patch("shomer.core.settings.get_settings")
    @patch("shomer.core.security.AESEncryption")
    @patch("shomer.services.jwk_service.JWKService")
    def test_revokes_key(
        self,
        mock_svc_cls: MagicMock,
        _mock_aes: MagicMock,
        _mock_settings: MagicMock,
        _mock_rbac: MagicMock,
    ) -> None:
        """Revokes a key and returns confirmation."""

        async def _run() -> None:
            revoked = _mock_jwk(kid="shomer-old", status_val="revoked")
            mock_svc = AsyncMock()
            mock_svc.revoke.return_value = revoked
            mock_svc_cls.return_value = mock_svc

            db = AsyncMock()
            resp = await revoke_key("shomer-old", db)
            data = json.loads(bytes(resp.body))
            assert data["kid"] == "shomer-old"
            assert data["status"] == "revoked"
            assert data["message"] == "Key revoked successfully"

        asyncio.run(_run())

    @patch("shomer.routes.admin_jwks.require_scope")
    @patch("shomer.core.settings.get_settings")
    @patch("shomer.core.security.AESEncryption")
    @patch("shomer.services.jwk_service.JWKService")
    def test_not_found_returns_404(
        self,
        mock_svc_cls: MagicMock,
        _mock_aes: MagicMock,
        _mock_settings: MagicMock,
        _mock_rbac: MagicMock,
    ) -> None:
        """Returns 404 when key not found."""

        async def _run() -> None:
            mock_svc = AsyncMock()
            mock_svc.revoke.return_value = None
            mock_svc_cls.return_value = mock_svc

            db = AsyncMock()
            try:
                await revoke_key("nonexistent", db)
                raise AssertionError("Expected HTTPException")
            except HTTPException as exc:
                assert exc.status_code == 404

        asyncio.run(_run())

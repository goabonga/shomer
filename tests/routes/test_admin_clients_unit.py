# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for admin OAuth2 clients API routes."""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from shomer.routes.admin_clients import (
    create_client,
    delete_client,
    get_client,
    list_clients,
    rotate_client_secret,
    update_client,
)


def _mock_client(
    client_id: str = "test-client",
    client_name: str = "Test App",
    is_active: bool = True,
) -> MagicMock:
    """Create a mock OAuth2Client."""
    c = MagicMock()
    c.id = uuid.uuid4()
    c.client_id = client_id
    c.client_name = client_name
    c.client_type = MagicMock(value="confidential")
    c.token_endpoint_auth_method = MagicMock(value="client_secret_basic")
    c.redirect_uris = ["https://example.com/cb"]
    c.grant_types = ["authorization_code"]
    c.response_types = ["code"]
    c.scopes = ["openid"]
    c.contacts = []
    c.logo_uri = None
    c.tos_uri = None
    c.policy_uri = None
    c.is_active = is_active
    c.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return c


class TestListClients:
    """Tests for GET /admin/clients."""

    @patch("shomer.routes.admin_clients.require_scope")
    def test_returns_paginated_clients(self, _mock_rbac: MagicMock) -> None:
        """Returns a paginated list of clients."""

        async def _run() -> None:
            mock_client = _mock_client()

            count_result = MagicMock()
            count_result.scalar.return_value = 1

            scalars_mock = MagicMock()
            scalars_mock.all.return_value = [mock_client]
            list_result = MagicMock()
            list_result.scalars.return_value = scalars_mock

            db = AsyncMock()
            db.execute.side_effect = [count_result, list_result]

            resp = await list_clients(db, page=1, page_size=20)
            data = json.loads(bytes(resp.body))
            assert data["total"] == 1
            assert len(data["items"]) == 1
            assert data["items"][0]["client_id"] == "test-client"
            assert data["items"][0]["client_type"] == "confidential"

        asyncio.run(_run())

    @patch("shomer.routes.admin_clients.require_scope")
    def test_empty_list(self, _mock_rbac: MagicMock) -> None:
        """Returns empty list."""

        async def _run() -> None:
            count_result = MagicMock()
            count_result.scalar.return_value = 0
            scalars_mock = MagicMock()
            scalars_mock.all.return_value = []
            list_result = MagicMock()
            list_result.scalars.return_value = scalars_mock

            db = AsyncMock()
            db.execute.side_effect = [count_result, list_result]

            resp = await list_clients(db, page=1, page_size=20)
            data = json.loads(bytes(resp.body))
            assert data["total"] == 0
            assert data["items"] == []

        asyncio.run(_run())


class TestGetClient:
    """Tests for GET /admin/clients/{id}."""

    @patch("shomer.routes.admin_clients.require_scope")
    def test_returns_client_detail(self, _mock_rbac: MagicMock) -> None:
        """Returns full client details."""

        async def _run() -> None:
            mock = _mock_client()
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock

            db = AsyncMock()
            db.execute.return_value = result

            resp = await get_client(str(mock.id), db)
            data = json.loads(bytes(resp.body))
            assert data["client_id"] == "test-client"
            assert data["redirect_uris"] == ["https://example.com/cb"]
            assert data["token_endpoint_auth_method"] == "client_secret_basic"

        asyncio.run(_run())

    @patch("shomer.routes.admin_clients.require_scope")
    def test_invalid_uuid_returns_400(self, _mock_rbac: MagicMock) -> None:
        """Returns 400 for invalid UUID."""

        async def _run() -> None:
            try:
                await get_client("bad", AsyncMock())
                raise AssertionError("Expected HTTPException")
            except HTTPException as exc:
                assert exc.status_code == 400

        asyncio.run(_run())

    @patch("shomer.routes.admin_clients.require_scope")
    def test_not_found_returns_404(self, _mock_rbac: MagicMock) -> None:
        """Returns 404 when not found."""

        async def _run() -> None:
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db = AsyncMock()
            db.execute.return_value = result

            try:
                await get_client(str(uuid.uuid4()), db)
                raise AssertionError("Expected HTTPException")
            except HTTPException as exc:
                assert exc.status_code == 404

        asyncio.run(_run())


class TestCreateClient:
    """Tests for POST /admin/clients."""

    @patch("shomer.routes.admin_clients.require_scope")
    @patch("shomer.services.oauth2_client_service.OAuth2ClientService")
    def test_creates_confidential_client(
        self, mock_svc_cls: MagicMock, _mock_rbac: MagicMock
    ) -> None:
        """Creates a confidential client and returns secret."""

        async def _run() -> None:
            mock_client = _mock_client()
            mock_svc = AsyncMock()
            mock_svc.create_client.return_value = (mock_client, "raw-secret-value")
            mock_svc_cls.return_value = mock_svc

            from shomer.routes.admin_clients import AdminCreateClientRequest

            body = AdminCreateClientRequest(
                client_name="My App",
                client_type="confidential",
                redirect_uris=["https://app.example.com/cb"],
            )
            resp = await create_client(body, AsyncMock())
            assert resp.status_code == 201
            data = json.loads(bytes(resp.body))
            assert data["client_secret"] == "raw-secret-value"
            assert data["message"] == "Client created successfully"

        asyncio.run(_run())


class TestUpdateClient:
    """Tests for PUT /admin/clients/{id}."""

    @patch("shomer.routes.admin_clients.require_scope")
    def test_updates_client(self, _mock_rbac: MagicMock) -> None:
        """Updates client name and returns success."""

        async def _run() -> None:
            mock = _mock_client()
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock
            db = AsyncMock()
            db.execute.return_value = result

            from shomer.routes.admin_clients import AdminUpdateClientRequest

            body = AdminUpdateClientRequest(client_name="Updated Name")
            resp = await update_client(str(mock.id), body, db)
            data = json.loads(bytes(resp.body))
            assert data["client_name"] == "Updated Name"
            assert data["message"] == "Client updated successfully"
            db.flush.assert_awaited_once()

        asyncio.run(_run())

    @patch("shomer.routes.admin_clients.require_scope")
    def test_not_found_returns_404(self, _mock_rbac: MagicMock) -> None:
        """Returns 404 when not found."""

        async def _run() -> None:
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db = AsyncMock()
            db.execute.return_value = result

            from shomer.routes.admin_clients import AdminUpdateClientRequest

            body = AdminUpdateClientRequest(is_active=False)
            try:
                await update_client(str(uuid.uuid4()), body, db)
                raise AssertionError("Expected HTTPException")
            except HTTPException as exc:
                assert exc.status_code == 404

        asyncio.run(_run())


class TestDeleteClient:
    """Tests for DELETE /admin/clients/{id}."""

    @patch("shomer.routes.admin_clients.require_scope")
    def test_deletes_client(self, _mock_rbac: MagicMock) -> None:
        """Deletes client and returns confirmation."""

        async def _run() -> None:
            mock = _mock_client()
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock
            db = AsyncMock()
            db.execute.return_value = result

            resp = await delete_client(str(mock.id), db)
            data = json.loads(bytes(resp.body))
            assert data["message"] == "Client deleted successfully"
            db.delete.assert_awaited_once_with(mock)

        asyncio.run(_run())

    @patch("shomer.routes.admin_clients.require_scope")
    def test_not_found_returns_404(self, _mock_rbac: MagicMock) -> None:
        """Returns 404 when not found."""

        async def _run() -> None:
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db = AsyncMock()
            db.execute.return_value = result

            try:
                await delete_client(str(uuid.uuid4()), db)
                raise AssertionError("Expected HTTPException")
            except HTTPException as exc:
                assert exc.status_code == 404

        asyncio.run(_run())


class TestRotateSecret:
    """Tests for POST /admin/clients/{id}/rotate-secret."""

    @patch("shomer.routes.admin_clients.require_scope")
    @patch("shomer.services.oauth2_client_service.OAuth2ClientService")
    def test_rotates_secret(
        self, mock_svc_cls: MagicMock, _mock_rbac: MagicMock
    ) -> None:
        """Rotates secret for confidential client."""

        async def _run() -> None:
            mock = _mock_client()
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock

            mock_svc = AsyncMock()
            mock_svc.rotate_secret.return_value = (mock, "new-secret")
            mock_svc_cls.return_value = mock_svc

            db = AsyncMock()
            db.execute.return_value = result

            resp = await rotate_client_secret(str(mock.id), db)
            data = json.loads(bytes(resp.body))
            assert data["client_secret"] == "new-secret"
            assert data["message"] == "Client secret rotated successfully"

        asyncio.run(_run())

    @patch("shomer.routes.admin_clients.require_scope")
    def test_public_client_returns_400(self, _mock_rbac: MagicMock) -> None:
        """Returns 400 for public client."""

        async def _run() -> None:
            mock = _mock_client()
            mock.client_type = MagicMock(value="public")
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock

            db = AsyncMock()
            db.execute.return_value = result

            try:
                await rotate_client_secret(str(mock.id), db)
                raise AssertionError("Expected HTTPException")
            except HTTPException as exc:
                assert exc.status_code == 400

        asyncio.run(_run())

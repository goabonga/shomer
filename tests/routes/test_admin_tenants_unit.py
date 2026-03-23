# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for admin tenants API routes."""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from shomer.routes.admin_tenants import (
    add_member,
    create_tenant,
    delete_tenant,
    get_domains,
    get_tenant,
    list_idps,
    list_members,
    list_tenants,
    update_branding,
    update_domains,
)


def _mock_tenant(slug: str = "acme", name: str = "Acme Corp") -> MagicMock:
    """Create a mock Tenant."""
    t = MagicMock()
    t.id = uuid.uuid4()
    t.slug = slug
    t.name = name
    t.display_name = name
    t.is_active = True
    t.is_platform = False
    t.trust_mode = MagicMock(value="none")
    t.custom_domain = None
    t.settings = {}
    t.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return t


class TestListTenants:
    """Tests for GET /admin/tenants."""

    @patch("shomer.routes.admin_tenants.require_scope")
    def test_returns_paginated_tenants(self, _: MagicMock) -> None:
        """Returns paginated list."""

        async def _run() -> None:
            t = _mock_tenant()
            count_result = MagicMock()
            count_result.scalar.return_value = 1
            scalars = MagicMock()
            scalars.all.return_value = [t]
            list_result = MagicMock()
            list_result.scalars.return_value = scalars

            db = AsyncMock()
            db.execute.side_effect = [count_result, list_result]

            resp = await list_tenants(db, page=1, page_size=20)
            data = json.loads(bytes(resp.body))
            assert data["total"] == 1
            assert data["items"][0]["slug"] == "acme"

        asyncio.run(_run())


class TestCreateTenant:
    """Tests for POST /admin/tenants."""

    @patch("shomer.routes.admin_tenants.require_scope")
    def test_creates_tenant(self, _: MagicMock) -> None:
        """Creates a new tenant."""

        async def _run() -> None:
            check = MagicMock()
            check.scalar_one_or_none.return_value = None
            db = AsyncMock()
            db.execute.return_value = check

            from shomer.routes.admin_tenants import TenantCreateRequest

            body = TenantCreateRequest(slug="new-co", name="New Co")
            resp = await create_tenant(body, db)
            assert resp.status_code == 201

        asyncio.run(_run())

    @patch("shomer.routes.admin_tenants.require_scope")
    def test_duplicate_slug_returns_409(self, _: MagicMock) -> None:
        """Returns 409 for duplicate slug."""

        async def _run() -> None:
            check = MagicMock()
            check.scalar_one_or_none.return_value = MagicMock()
            db = AsyncMock()
            db.execute.return_value = check

            from shomer.routes.admin_tenants import TenantCreateRequest

            body = TenantCreateRequest(slug="dup", name="Dup")
            try:
                await create_tenant(body, db)
                raise AssertionError("Expected HTTPException")
            except HTTPException as exc:
                assert exc.status_code == 409

        asyncio.run(_run())


class TestGetTenant:
    """Tests for GET /admin/tenants/{id}."""

    @patch("shomer.routes.admin_tenants.require_scope")
    def test_returns_tenant_detail(self, _: MagicMock) -> None:
        """Returns tenant with settings."""

        async def _run() -> None:
            t = _mock_tenant()
            result = MagicMock()
            result.scalar_one_or_none.return_value = t
            db = AsyncMock()
            db.execute.return_value = result

            resp = await get_tenant(str(t.id), db)
            data = json.loads(bytes(resp.body))
            assert data["slug"] == "acme"
            assert "settings" in data

        asyncio.run(_run())

    @patch("shomer.routes.admin_tenants.require_scope")
    def test_not_found_returns_404(self, _: MagicMock) -> None:
        """Returns 404."""

        async def _run() -> None:
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db = AsyncMock()
            db.execute.return_value = result
            try:
                await get_tenant(str(uuid.uuid4()), db)
                raise AssertionError("Expected HTTPException")
            except HTTPException as exc:
                assert exc.status_code == 404

        asyncio.run(_run())


class TestDeleteTenant:
    """Tests for DELETE /admin/tenants/{id}."""

    @patch("shomer.routes.admin_tenants.require_scope")
    def test_cannot_delete_platform(self, _: MagicMock) -> None:
        """Returns 400 for platform tenant."""

        async def _run() -> None:
            t = _mock_tenant()
            t.is_platform = True
            result = MagicMock()
            result.scalar_one_or_none.return_value = t
            db = AsyncMock()
            db.execute.return_value = result
            try:
                await delete_tenant(str(t.id), db)
                raise AssertionError("Expected HTTPException")
            except HTTPException as exc:
                assert exc.status_code == 400

        asyncio.run(_run())

    @patch("shomer.routes.admin_tenants.require_scope")
    def test_deletes_tenant(self, _: MagicMock) -> None:
        """Deletes a non-platform tenant."""

        async def _run() -> None:
            t = _mock_tenant()
            result = MagicMock()
            result.scalar_one_or_none.return_value = t
            db = AsyncMock()
            db.execute.return_value = result

            resp = await delete_tenant(str(t.id), db)
            data = json.loads(bytes(resp.body))
            assert data["message"] == "Tenant deleted successfully"
            db.delete.assert_awaited_once_with(t)

        asyncio.run(_run())


class TestListMembers:
    """Tests for GET /admin/tenants/{id}/members."""

    @patch("shomer.routes.admin_tenants.require_scope")
    def test_returns_members(self, _: MagicMock) -> None:
        """Returns member list."""

        async def _run() -> None:
            m = MagicMock()
            m.id = uuid.uuid4()
            m.user_id = uuid.uuid4()
            m.role = "member"
            m.joined_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
            scalars = MagicMock()
            scalars.all.return_value = [m]
            result = MagicMock()
            result.scalars.return_value = scalars
            db = AsyncMock()
            db.execute.return_value = result

            resp = await list_members(str(uuid.uuid4()), db)
            data = json.loads(bytes(resp.body))
            assert data["total"] == 1
            assert data["items"][0]["role"] == "member"

        asyncio.run(_run())


class TestAddMember:
    """Tests for POST /admin/tenants/{id}/members."""

    @patch("shomer.routes.admin_tenants.require_scope")
    def test_adds_member(self, _: MagicMock) -> None:
        """Adds a member."""

        async def _run() -> None:
            check = MagicMock()
            check.scalar_one_or_none.return_value = None
            db = AsyncMock()
            db.execute.return_value = check

            from shomer.routes.admin_tenants import MemberRequest

            body = MemberRequest(user_id=str(uuid.uuid4()))
            resp = await add_member(str(uuid.uuid4()), body, db)
            assert resp.status_code == 201

        asyncio.run(_run())

    @patch("shomer.routes.admin_tenants.require_scope")
    def test_duplicate_returns_409(self, _: MagicMock) -> None:
        """Returns 409 for duplicate member."""

        async def _run() -> None:
            check = MagicMock()
            check.scalar_one_or_none.return_value = MagicMock()
            db = AsyncMock()
            db.execute.return_value = check

            from shomer.routes.admin_tenants import MemberRequest

            body = MemberRequest(user_id=str(uuid.uuid4()))
            try:
                await add_member(str(uuid.uuid4()), body, db)
                raise AssertionError("Expected HTTPException")
            except HTTPException as exc:
                assert exc.status_code == 409

        asyncio.run(_run())


class TestUpdateBranding:
    """Tests for PUT /admin/tenants/{id}/branding."""

    @patch("shomer.routes.admin_tenants.require_scope")
    def test_updates_branding(self, _: MagicMock) -> None:
        """Updates branding fields."""

        async def _run() -> None:
            branding = MagicMock()
            branding.logo_url = None
            branding.primary_color = None
            branding.secondary_color = None
            result = MagicMock()
            result.scalar_one_or_none.return_value = branding
            db = AsyncMock()
            db.execute.return_value = result

            from shomer.routes.admin_tenants import BrandingUpdateRequest

            body = BrandingUpdateRequest(primary_color="#ff0000")
            resp = await update_branding(str(uuid.uuid4()), body, db)
            data = json.loads(bytes(resp.body))
            assert data["message"] == "Branding updated successfully"
            assert branding.primary_color == "#ff0000"

        asyncio.run(_run())


class TestListIdPs:
    """Tests for GET /admin/tenants/{id}/idps."""

    @patch("shomer.routes.admin_tenants.require_scope")
    def test_returns_idps(self, _: MagicMock) -> None:
        """Returns IdP list."""

        async def _run() -> None:
            idp = MagicMock()
            idp.id = uuid.uuid4()
            idp.name = "Google"
            idp.provider_type = MagicMock(value="google")
            idp.client_id = "goog-123"
            idp.is_active = True
            scalars = MagicMock()
            scalars.all.return_value = [idp]
            result = MagicMock()
            result.scalars.return_value = scalars
            db = AsyncMock()
            db.execute.return_value = result

            resp = await list_idps(str(uuid.uuid4()), db)
            data = json.loads(bytes(resp.body))
            assert data["total"] == 1
            assert data["items"][0]["name"] == "Google"

        asyncio.run(_run())


class TestGetDomains:
    """Tests for GET /admin/tenants/{id}/domains."""

    @patch("shomer.routes.admin_tenants.require_scope")
    def test_returns_domain(self, _: MagicMock) -> None:
        """Returns domain info."""

        async def _run() -> None:
            t = _mock_tenant()
            t.custom_domain = "auth.acme.com"
            result = MagicMock()
            result.scalar_one_or_none.return_value = t
            db = AsyncMock()
            db.execute.return_value = result

            resp = await get_domains(str(t.id), db)
            data = json.loads(bytes(resp.body))
            assert data["custom_domain"] == "auth.acme.com"

        asyncio.run(_run())


class TestUpdateDomains:
    """Tests for PUT /admin/tenants/{id}/domains."""

    @patch("shomer.routes.admin_tenants.require_scope")
    def test_updates_domain(self, _: MagicMock) -> None:
        """Updates custom domain."""

        async def _run() -> None:
            t = _mock_tenant()
            result = MagicMock()
            result.scalar_one_or_none.return_value = t
            db = AsyncMock()
            db.execute.return_value = result

            from shomer.routes.admin_tenants import DomainUpdateRequest

            body = DomainUpdateRequest(custom_domain="new.acme.com")
            resp = await update_domains(str(t.id), body, db)
            data = json.loads(bytes(resp.body))
            assert data["custom_domain"] == "new.acme.com"
            assert data["message"] == "Domain updated successfully"

        asyncio.run(_run())

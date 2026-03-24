# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for organisation settings UI routes."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from shomer.routes.organisation_settings_ui import (
    _get_session_user,
    settings_organisations,
)


def _req(cookies: dict[str, str] | None = None) -> MagicMock:
    """Build a mock Request with optional cookies."""
    cookie_data = cookies or {}
    r = MagicMock()
    r.cookies = MagicMock()
    r.cookies.get = lambda k, d=None: cookie_data.get(k, d)
    return r


def _mock_user() -> MagicMock:
    """Build a mock authenticated user."""
    u = MagicMock()
    u.id = uuid.uuid4()
    u.username = "testuser"
    u.profile = MagicMock(name="Test", locale="en-US")
    e = MagicMock()
    e.email = "test@example.com"
    e.is_primary = True
    e.is_verified = True
    u.emails = [e]
    return u


def _mock_membership(
    tenant_name: str = "acme",
    role: str = "member",
) -> MagicMock:
    """Build a mock TenantMember with associated Tenant."""
    tenant = MagicMock()
    tenant.id = uuid.uuid4()
    tenant.slug = tenant_name
    tenant.name = tenant_name.capitalize()
    tenant.display_name = f"{tenant_name.capitalize()} Corp"
    tenant.is_active = True
    tenant.is_platform = False

    membership = MagicMock()
    membership.tenant = tenant
    membership.role = role
    membership.joined_at = datetime(2025, 1, 15, tzinfo=timezone.utc)
    return membership


class TestGetSessionUser:
    """Tests for _get_session_user()."""

    def test_no_cookie_returns_none(self) -> None:
        """Return None when no session cookie is present."""

        async def _run() -> None:
            result = await _get_session_user(_req(), AsyncMock())
            assert result is None

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui.SessionService")
    def test_invalid_session_returns_none(self, mock_cls: MagicMock) -> None:
        """Return None when session token is invalid."""

        async def _run() -> None:
            mock_svc = AsyncMock()
            mock_svc.validate.return_value = None
            mock_cls.return_value = mock_svc
            result = await _get_session_user(_req({"session_id": "bad"}), AsyncMock())
            assert result is None

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui.SessionService")
    def test_valid_session_returns_tuple(self, mock_cls: MagicMock) -> None:
        """Return (session, user) for a valid session."""

        async def _run() -> None:
            mock_session = MagicMock(user_id=uuid.uuid4())
            mock_svc = AsyncMock()
            mock_svc.validate.return_value = mock_session
            mock_cls.return_value = mock_svc

            db = AsyncMock()
            mock_user = _mock_user()
            result_mock = MagicMock()
            result_mock.scalar_one_or_none.return_value = mock_user
            db.execute.return_value = result_mock

            result = await _get_session_user(_req({"session_id": "good"}), db)
            assert result is not None
            assert result[1].username == "testuser"

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui.SessionService")
    def test_user_not_found_returns_none(self, mock_cls: MagicMock) -> None:
        """Return None when session is valid but user is missing."""

        async def _run() -> None:
            mock_session = MagicMock(user_id=uuid.uuid4())
            mock_svc = AsyncMock()
            mock_svc.validate.return_value = mock_session
            mock_cls.return_value = mock_svc

            db = AsyncMock()
            result_mock = MagicMock()
            result_mock.scalar_one_or_none.return_value = None
            db.execute.return_value = result_mock

            result = await _get_session_user(_req({"session_id": "good"}), db)
            assert result is None

        asyncio.run(_run())


class TestSettingsOrganisations:
    """Tests for GET /ui/settings/organisations."""

    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        """Redirect to login when not authenticated."""

        async def _run() -> None:
            mock_auth.return_value = None
            resp = await settings_organisations(_req(), AsyncMock())
            assert resp.status_code == 302
            assert "/ui/login" in resp.headers["location"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_authenticated_renders_orgs(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Render organisations page with membership list."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)

            m1 = _mock_membership("acme", "owner")
            m2 = _mock_membership("beta", "member")

            db = AsyncMock()
            scalars_mock = MagicMock()
            scalars_mock.all.return_value = [m1, m2]
            result_mock = MagicMock()
            result_mock.scalars.return_value = scalars_mock
            db.execute.return_value = result_mock

            mock_render.return_value = MagicMock()

            await settings_organisations(_req({"session_id": "tok"}), db)

            mock_render.assert_called_once()
            call_args = mock_render.call_args
            ctx = call_args[0][2]
            assert ctx["section"] == "organisations"
            assert len(ctx["organisations"]) == 2
            assert ctx["organisations"][0]["slug"] == "acme"
            assert ctx["organisations"][0]["role"] == "owner"
            assert ctx["organisations"][1]["slug"] == "beta"

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_authenticated_no_orgs(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Render organisations page with empty list."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)

            db = AsyncMock()
            scalars_mock = MagicMock()
            scalars_mock.all.return_value = []
            result_mock = MagicMock()
            result_mock.scalars.return_value = scalars_mock
            db.execute.return_value = result_mock

            mock_render.return_value = MagicMock()

            await settings_organisations(_req({"session_id": "tok"}), db)

            mock_render.assert_called_once()
            ctx = mock_render.call_args[0][2]
            assert ctx["organisations"] == []

        asyncio.run(_run())

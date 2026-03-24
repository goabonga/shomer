# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for organisation settings UI routes."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from shomer.routes.organisation_settings_ui import (
    _SLUG_RE,
    _get_membership,
    _get_session_user,
    _parse_uuid,
    settings_organisation_create,
    settings_organisation_detail,
    settings_organisation_edit,
    settings_organisation_new,
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


class TestSlugRegex:
    """Tests for _SLUG_RE validation."""

    def test_valid_slugs(self) -> None:
        """Accept valid slugs."""
        for slug in ("acme", "my-org", "a1b2c3", "org-123-test"):
            assert _SLUG_RE.match(slug), f"Expected valid: {slug}"

    def test_invalid_slugs(self) -> None:
        """Reject invalid slugs."""
        for slug in ("", "a", "AB", "-start", "end-", "has space", "UPPER"):
            assert not _SLUG_RE.match(slug), f"Expected invalid: {slug}"


class TestSettingsOrganisationNew:
    """Tests for GET /ui/settings/organisations/new."""

    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        """Redirect to login when not authenticated."""

        async def _run() -> None:
            mock_auth.return_value = None
            resp = await settings_organisation_new(_req(), AsyncMock())
            assert resp.status_code == 302
            assert "/ui/login" in resp.headers["location"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_authenticated_renders_form(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Render the create organisation form."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            mock_render.return_value = MagicMock()

            await settings_organisation_new(_req({"session_id": "tok"}), AsyncMock())

            mock_render.assert_called_once()
            ctx = mock_render.call_args[0][2]
            assert ctx["section"] == "organisations"
            assert "trust_modes" in ctx
            assert ctx["error"] is None

        asyncio.run(_run())


class TestSettingsOrganisationCreate:
    """Tests for POST /ui/settings/organisations/new."""

    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        """Redirect to login when not authenticated."""

        async def _run() -> None:
            mock_auth.return_value = None
            resp = await settings_organisation_create(
                _req(), AsyncMock(), slug="test", name="Test"
            )
            assert resp.status_code == 302
            assert "/ui/login" in resp.headers["location"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_invalid_slug_shows_error(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Show error when slug is invalid."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            mock_render.return_value = MagicMock()

            await settings_organisation_create(
                _req({"session_id": "tok"}),
                AsyncMock(),
                slug="A",
                name="Test",
            )

            mock_render.assert_called_once()
            ctx = mock_render.call_args[0][2]
            assert "Invalid slug" in ctx["error"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_duplicate_slug_shows_error(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Show error when slug already exists."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            mock_render.return_value = MagicMock()

            db = AsyncMock()
            result_mock = MagicMock()
            result_mock.scalar_one_or_none.return_value = MagicMock()  # existing
            db.execute.return_value = result_mock

            await settings_organisation_create(
                _req({"session_id": "tok"}),
                db,
                slug="acme-corp",
                name="Acme",
            )

            mock_render.assert_called_once()
            ctx = mock_render.call_args[0][2]
            assert "already taken" in ctx["error"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_invalid_trust_mode_shows_error(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Show error for invalid trust mode."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            mock_render.return_value = MagicMock()

            db = AsyncMock()
            result_mock = MagicMock()
            result_mock.scalar_one_or_none.return_value = None
            db.execute.return_value = result_mock

            await settings_organisation_create(
                _req({"session_id": "tok"}),
                db,
                slug="acme-corp",
                name="Acme",
                trust_mode="invalid",
            )

            mock_render.assert_called_once()
            ctx = mock_render.call_args[0][2]
            assert "Invalid trust mode" in ctx["error"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_success_redirects(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Redirect to org detail on successful creation."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)

            db = AsyncMock()
            result_mock = MagicMock()
            result_mock.scalar_one_or_none.return_value = None
            db.execute.return_value = result_mock

            resp = await settings_organisation_create(
                _req({"session_id": "tok"}),
                db,
                slug="acme-corp",
                name="Acme Corp",
                display_name="Acme Corp Inc.",
                trust_mode="none",
            )

            mock_render.assert_not_called()
            assert resp.status_code == 302
            assert "/ui/settings/organisations/" in resp.headers["location"]
            assert db.add.call_count == 2  # tenant + membership
            assert db.flush.call_count == 2

        asyncio.run(_run())


class TestParseUuid:
    """Tests for _parse_uuid()."""

    def test_valid_uuid(self) -> None:
        """Parse a valid UUID string."""
        uid = uuid.uuid4()
        assert _parse_uuid(str(uid)) == uid

    def test_invalid_uuid(self) -> None:
        """Return None for an invalid UUID."""
        assert _parse_uuid("not-a-uuid") is None


class TestGetMembership:
    """Tests for _get_membership()."""

    def test_no_membership(self) -> None:
        """Return None when user is not a member."""

        async def _run() -> None:
            db = AsyncMock()
            result_mock = MagicMock()
            result_mock.scalar_one_or_none.return_value = None
            db.execute.return_value = result_mock

            result = await _get_membership(db, uuid.uuid4(), uuid.uuid4())
            assert result is None

        asyncio.run(_run())

    def test_has_membership(self) -> None:
        """Return (membership, tenant) when user is a member."""

        async def _run() -> None:
            tenant = MagicMock()
            membership = MagicMock()
            membership.tenant = tenant

            db = AsyncMock()
            result_mock = MagicMock()
            result_mock.scalar_one_or_none.return_value = membership
            db.execute.return_value = result_mock

            result = await _get_membership(db, uuid.uuid4(), uuid.uuid4())
            assert result is not None
            assert result[0] is membership
            assert result[1] is tenant

        asyncio.run(_run())


class TestSettingsOrganisationDetail:
    """Tests for GET /ui/settings/organisations/{org_id}."""

    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        """Redirect to login when not authenticated."""

        async def _run() -> None:
            mock_auth.return_value = None
            resp = await settings_organisation_detail(
                _req(), str(uuid.uuid4()), AsyncMock()
            )
            assert resp.status_code == 302
            assert "/ui/login" in resp.headers["location"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_invalid_uuid_shows_error(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Show error for invalid UUID."""

        async def _run() -> None:
            mock_auth.return_value = (MagicMock(), _mock_user())
            mock_render.return_value = MagicMock()

            await settings_organisation_detail(
                _req({"session_id": "tok"}), "bad-id", AsyncMock()
            )

            ctx = mock_render.call_args[0][2]
            assert "Invalid" in ctx["error"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_not_member_shows_error(
        self,
        mock_auth: AsyncMock,
        mock_membership: AsyncMock,
        mock_render: MagicMock,
    ) -> None:
        """Show error when user is not a member."""

        async def _run() -> None:
            mock_auth.return_value = (MagicMock(), _mock_user())
            mock_membership.return_value = None
            mock_render.return_value = MagicMock()

            await settings_organisation_detail(
                _req({"session_id": "tok"}), str(uuid.uuid4()), AsyncMock()
            )

            ctx = mock_render.call_args[0][2]
            assert "not found" in ctx["error"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_member_renders_detail(
        self,
        mock_auth: AsyncMock,
        mock_membership: AsyncMock,
        mock_render: MagicMock,
    ) -> None:
        """Render detail page for a member."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)

            tenant = MagicMock()
            tenant.id = uuid.uuid4()
            tenant.slug = "acme"
            tenant.name = "Acme"
            tenant.display_name = "Acme Corp"
            tenant.custom_domain = None
            tenant.is_active = True
            tenant.is_platform = False
            tenant.trust_mode = MagicMock(value="none")
            tenant.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)

            membership = MagicMock()
            membership.role = "owner"
            membership.tenant = tenant

            mock_membership.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            await settings_organisation_detail(
                _req({"session_id": "tok"}), str(tenant.id), AsyncMock()
            )

            ctx = mock_render.call_args[0][2]
            assert ctx["org"]["slug"] == "acme"
            assert ctx["role"] == "owner"
            assert ctx["error"] is None

        asyncio.run(_run())


class TestSettingsOrganisationEdit:
    """Tests for POST /ui/settings/organisations/{org_id}."""

    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        """Redirect to login when not authenticated."""

        async def _run() -> None:
            mock_auth.return_value = None
            resp = await settings_organisation_edit(
                _req(),
                str(uuid.uuid4()),
                AsyncMock(),
                name="X",
                display_name="X",
                trust_mode="none",
            )
            assert resp.status_code == 302

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_member_cannot_edit(
        self,
        mock_auth: AsyncMock,
        mock_membership: AsyncMock,
        mock_render: MagicMock,
    ) -> None:
        """Show error when a regular member tries to edit."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)

            tenant = MagicMock()
            tenant.id = uuid.uuid4()
            tenant.slug = "acme"
            tenant.name = "Acme"
            tenant.display_name = "Acme"
            tenant.custom_domain = None
            tenant.is_active = True
            tenant.is_platform = False
            tenant.trust_mode = MagicMock(value="none")
            tenant.created_at = None

            membership = MagicMock()
            membership.role = "member"
            membership.tenant = tenant

            mock_membership.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            await settings_organisation_edit(
                _req({"session_id": "tok"}),
                str(tenant.id),
                AsyncMock(),
                name="New",
                display_name="New",
                trust_mode="none",
            )

            ctx = mock_render.call_args[0][2]
            assert "permission" in ctx["error"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_owner_can_edit(
        self,
        mock_auth: AsyncMock,
        mock_membership: AsyncMock,
        mock_render: MagicMock,
    ) -> None:
        """Owner can successfully edit the organisation."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)

            tenant = MagicMock()
            tenant.id = uuid.uuid4()
            tenant.slug = "acme"
            tenant.name = "Acme"
            tenant.display_name = "Acme"
            tenant.custom_domain = None
            tenant.is_active = True
            tenant.is_platform = False
            tenant.trust_mode = MagicMock(value="none")
            tenant.created_at = None

            membership = MagicMock()
            membership.role = "owner"
            membership.tenant = tenant

            mock_membership.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            db = AsyncMock()
            await settings_organisation_edit(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                name="New Name",
                display_name="New Display",
                trust_mode="all",
            )

            ctx = mock_render.call_args[0][2]
            assert ctx["success"] == "Organisation updated successfully."
            assert tenant.name == "New Name"
            assert tenant.display_name == "New Display"
            db.flush.assert_awaited_once()

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_invalid_trust_mode(
        self,
        mock_auth: AsyncMock,
        mock_membership: AsyncMock,
        mock_render: MagicMock,
    ) -> None:
        """Show error for invalid trust mode."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)

            tenant = MagicMock()
            tenant.id = uuid.uuid4()
            tenant.slug = "acme"
            tenant.name = "Acme"
            tenant.display_name = "Acme"
            tenant.custom_domain = None
            tenant.is_active = True
            tenant.is_platform = False
            tenant.trust_mode = MagicMock(value="none")
            tenant.created_at = None

            membership = MagicMock()
            membership.role = "owner"
            membership.tenant = tenant

            mock_membership.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            await settings_organisation_edit(
                _req({"session_id": "tok"}),
                str(tenant.id),
                AsyncMock(),
                name="Acme",
                display_name="Acme",
                trust_mode="invalid",
            )

            ctx = mock_render.call_args[0][2]
            assert "Invalid trust mode" in ctx["error"]

        asyncio.run(_run())

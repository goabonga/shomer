# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for organisation settings UI routes."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from shomer.routes.organisation_settings_ui import (
    _DOMAIN_RE,
    _SLUG_RE,
    _get_membership,
    _get_session_user,
    _parse_uuid,
    settings_organisation_create,
    settings_organisation_detail,
    settings_organisation_domains,
    settings_organisation_domains_update,
    settings_organisation_edit,
    settings_organisation_idps,
    settings_organisation_idps_action,
    settings_organisation_members,
    settings_organisation_members_action,
    settings_organisation_new,
    settings_organisation_roles,
    settings_organisation_roles_action,
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


def _mock_tenant(
    slug: str = "acme",
    custom_domain: str | None = None,
) -> MagicMock:
    """Build a mock Tenant."""
    tenant = MagicMock()
    tenant.id = uuid.uuid4()
    tenant.slug = slug
    tenant.name = slug.capitalize()
    tenant.display_name = f"{slug.capitalize()} Corp"
    tenant.custom_domain = custom_domain
    tenant.is_active = True
    tenant.is_platform = False
    tenant.trust_mode = MagicMock(value="none")
    tenant.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return tenant


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


class TestDomainRegex:
    """Tests for _DOMAIN_RE validation."""

    def test_valid_domains(self) -> None:
        """Accept valid domain names."""
        for d in ("example.com", "auth.example.com", "a.b.co"):
            assert _DOMAIN_RE.match(d), f"Expected valid: {d}"

    def test_invalid_domains(self) -> None:
        """Reject invalid domain names."""
        for d in ("", "localhost", "-bad.com", "no_under.com"):
            assert not _DOMAIN_RE.match(d), f"Expected invalid: {d}"


class TestSettingsOrganisationDomains:
    """Tests for GET /ui/settings/organisations/{org_id}/domains."""

    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        """Redirect to login when not authenticated."""

        async def _run() -> None:
            mock_auth.return_value = None
            resp = await settings_organisation_domains(
                _req(), str(uuid.uuid4()), AsyncMock()
            )
            assert resp.status_code == 302

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_renders_domain_page(
        self,
        mock_auth: AsyncMock,
        mock_mem: AsyncMock,
        mock_render: MagicMock,
    ) -> None:
        """Render domain page for a member."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant(custom_domain="auth.acme.com")
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            await settings_organisation_domains(
                _req({"session_id": "tok"}), str(tenant.id), AsyncMock()
            )

            ctx = mock_render.call_args[0][2]
            assert ctx["custom_domain"] == "auth.acme.com"
            assert ctx["error"] is None

        asyncio.run(_run())


class TestSettingsOrganisationDomainsUpdate:
    """Tests for POST /ui/settings/organisations/{org_id}/domains."""

    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        """Redirect to login when not authenticated."""

        async def _run() -> None:
            mock_auth.return_value = None
            resp = await settings_organisation_domains_update(
                _req(), str(uuid.uuid4()), AsyncMock(), custom_domain=""
            )
            assert resp.status_code == 302

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_member_cannot_update(
        self,
        mock_auth: AsyncMock,
        mock_mem: AsyncMock,
        mock_render: MagicMock,
    ) -> None:
        """Show error when regular member tries to update domain."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="member", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            await settings_organisation_domains_update(
                _req({"session_id": "tok"}),
                str(tenant.id),
                AsyncMock(),
                custom_domain="new.com",
            )

            ctx = mock_render.call_args[0][2]
            assert "permission" in ctx["error"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_invalid_domain_format(
        self,
        mock_auth: AsyncMock,
        mock_mem: AsyncMock,
        mock_render: MagicMock,
    ) -> None:
        """Show error for invalid domain format."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            await settings_organisation_domains_update(
                _req({"session_id": "tok"}),
                str(tenant.id),
                AsyncMock(),
                custom_domain="-invalid",
            )

            ctx = mock_render.call_args[0][2]
            assert "Invalid domain" in ctx["error"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_owner_sets_domain(
        self,
        mock_auth: AsyncMock,
        mock_mem: AsyncMock,
        mock_render: MagicMock,
    ) -> None:
        """Owner can set a custom domain."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            db = AsyncMock()
            dup_result = MagicMock()
            dup_result.scalar_one_or_none.return_value = None
            db.execute.return_value = dup_result

            await settings_organisation_domains_update(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                custom_domain="auth.acme.com",
            )

            ctx = mock_render.call_args[0][2]
            assert "updated" in ctx["success"]
            assert tenant.custom_domain == "auth.acme.com"

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_owner_removes_domain(
        self,
        mock_auth: AsyncMock,
        mock_mem: AsyncMock,
        mock_render: MagicMock,
    ) -> None:
        """Owner can remove a custom domain by submitting empty."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant(custom_domain="old.com")
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            db = AsyncMock()
            await settings_organisation_domains_update(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                custom_domain="",
            )

            ctx = mock_render.call_args[0][2]
            assert "removed" in ctx["success"]
            assert tenant.custom_domain is None

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_duplicate_domain_error(
        self,
        mock_auth: AsyncMock,
        mock_mem: AsyncMock,
        mock_render: MagicMock,
    ) -> None:
        """Show error when domain is used by another org."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            db = AsyncMock()
            dup_result = MagicMock()
            dup_result.scalar_one_or_none.return_value = MagicMock()  # duplicate
            db.execute.return_value = dup_result

            await settings_organisation_domains_update(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                custom_domain="taken.com",
            )

            ctx = mock_render.call_args[0][2]
            assert "already in use" in ctx["error"]

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


class TestSettingsOrganisationMembers:
    """Tests for GET /ui/settings/organisations/{org_id}/members."""

    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        """Redirect to login when not authenticated."""

        async def _run() -> None:
            mock_auth.return_value = None
            resp = await settings_organisation_members(
                _req(), str(uuid.uuid4()), AsyncMock()
            )
            assert resp.status_code == 302

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._list_members")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_renders_members_page(
        self,
        mock_auth: AsyncMock,
        mock_mem: AsyncMock,
        mock_list: AsyncMock,
        mock_render: MagicMock,
    ) -> None:
        """Render members page for a member."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_list.return_value = [
                {"user_id": str(user.id), "username": "alice", "role": "owner"}
            ]
            mock_render.return_value = MagicMock()

            await settings_organisation_members(
                _req({"session_id": "tok"}), str(tenant.id), AsyncMock()
            )

            ctx = mock_render.call_args[0][2]
            assert len(ctx["members"]) == 1
            assert ctx["error"] is None

        asyncio.run(_run())


class TestSettingsOrganisationMembersAction:
    """Tests for POST /ui/settings/organisations/{org_id}/members."""

    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        """Redirect to login when not authenticated."""

        async def _run() -> None:
            mock_auth.return_value = None
            resp = await settings_organisation_members_action(
                _req(), str(uuid.uuid4()), AsyncMock(), action="add"
            )
            assert resp.status_code == 302

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._list_members")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_member_cannot_manage(
        self,
        mock_auth: AsyncMock,
        mock_mem: AsyncMock,
        mock_list: AsyncMock,
        mock_render: MagicMock,
    ) -> None:
        """Show error when regular member tries to manage."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="member", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_list.return_value = []
            mock_render.return_value = MagicMock()

            await settings_organisation_members_action(
                _req({"session_id": "tok"}),
                str(tenant.id),
                AsyncMock(),
                action="add",
                email="new@example.com",
                member_role="member",
            )

            ctx = mock_render.call_args[0][2]
            assert "permission" in ctx["error"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._list_members")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_add_member_success(
        self,
        mock_auth: AsyncMock,
        mock_mem: AsyncMock,
        mock_list: AsyncMock,
        mock_render: MagicMock,
    ) -> None:
        """Owner can add a member by email."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_list.return_value = []
            mock_render.return_value = MagicMock()

            db = AsyncMock()
            # First call: find user by email
            user_email_result = MagicMock()
            user_email_mock = MagicMock(user_id=uuid.uuid4())
            user_email_result.scalar_one_or_none.return_value = user_email_mock
            # Second call: check existing membership
            existing_result = MagicMock()
            existing_result.scalar_one_or_none.return_value = None
            db.execute.side_effect = [user_email_result, existing_result]

            await settings_organisation_members_action(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                action="add",
                email="new@example.com",
                member_role="member",
            )

            ctx = mock_render.call_args[0][2]
            assert "added" in ctx["success"]
            db.add.assert_called_once()

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._list_members")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_add_member_not_found(
        self,
        mock_auth: AsyncMock,
        mock_mem: AsyncMock,
        mock_list: AsyncMock,
        mock_render: MagicMock,
    ) -> None:
        """Show error when email not found."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_list.return_value = []
            mock_render.return_value = MagicMock()

            db = AsyncMock()
            result_mock = MagicMock()
            result_mock.scalar_one_or_none.return_value = None
            db.execute.return_value = result_mock

            await settings_organisation_members_action(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                action="add",
                email="nobody@example.com",
                member_role="member",
            )

            ctx = mock_render.call_args[0][2]
            assert "No user found" in ctx["error"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._list_members")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_remove_member_success(
        self,
        mock_auth: AsyncMock,
        mock_mem: AsyncMock,
        mock_list: AsyncMock,
        mock_render: MagicMock,
    ) -> None:
        """Owner can remove a member."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_list.return_value = []
            mock_render.return_value = MagicMock()

            other_member = MagicMock()
            other_member.user_id = uuid.uuid4()  # different from user.id
            mid = uuid.uuid4()

            db = AsyncMock()
            result_mock = MagicMock()
            result_mock.scalar_one_or_none.return_value = other_member
            db.execute.return_value = result_mock

            await settings_organisation_members_action(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                action="remove",
                member_id=str(mid),
            )

            ctx = mock_render.call_args[0][2]
            assert "removed" in ctx["success"]
            db.delete.assert_called_once()

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._list_members")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_cannot_remove_self(
        self,
        mock_auth: AsyncMock,
        mock_mem: AsyncMock,
        mock_list: AsyncMock,
        mock_render: MagicMock,
    ) -> None:
        """Cannot remove yourself."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_list.return_value = []
            mock_render.return_value = MagicMock()

            self_member = MagicMock()
            self_member.user_id = user.id  # same as current user
            mid = uuid.uuid4()

            db = AsyncMock()
            result_mock = MagicMock()
            result_mock.scalar_one_or_none.return_value = self_member
            db.execute.return_value = result_mock

            await settings_organisation_members_action(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                action="remove",
                member_id=str(mid),
            )

            ctx = mock_render.call_args[0][2]
            assert "cannot remove yourself" in ctx["error"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._list_members")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_update_role_success(
        self,
        mock_auth: AsyncMock,
        mock_mem: AsyncMock,
        mock_list: AsyncMock,
        mock_render: MagicMock,
    ) -> None:
        """Owner can update another member's role."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_list.return_value = []
            mock_render.return_value = MagicMock()

            other_member = MagicMock()
            other_member.user_id = uuid.uuid4()
            mid = uuid.uuid4()

            db = AsyncMock()
            result_mock = MagicMock()
            result_mock.scalar_one_or_none.return_value = other_member
            db.execute.return_value = result_mock

            await settings_organisation_members_action(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                action="update_role",
                member_id=str(mid),
                member_role="admin",
            )

            ctx = mock_render.call_args[0][2]
            assert "updated" in ctx["success"]
            assert other_member.role == "admin"

        asyncio.run(_run())


class TestSettingsOrganisationRoles:
    """Tests for GET /ui/settings/organisations/{org_id}/roles."""

    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        """Redirect to login when not authenticated."""

        async def _run() -> None:
            mock_auth.return_value = None
            resp = await settings_organisation_roles(_req(), "some-id", AsyncMock())
            assert resp.status_code == 302
            assert "/ui/login" in resp.headers["location"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_invalid_org_id(self, mock_auth: AsyncMock, mock_render: MagicMock) -> None:
        """Show error for invalid org ID."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            mock_render.return_value = MagicMock()

            await settings_organisation_roles(
                _req({"session_id": "tok"}), "not-a-uuid", AsyncMock()
            )

            ctx = mock_render.call_args[0][2]
            assert "Invalid organisation ID" in ctx["error"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_not_member_shows_error(
        self, mock_auth: AsyncMock, mock_mem: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Show error when user is not a member."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            mock_mem.return_value = None
            mock_render.return_value = MagicMock()

            await settings_organisation_roles(
                _req({"session_id": "tok"}), str(uuid.uuid4()), AsyncMock()
            )

            ctx = mock_render.call_args[0][2]
            assert "not found" in ctx["error"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_renders_roles_list(
        self, mock_auth: AsyncMock, mock_mem: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Render roles page with list of custom roles."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            role1 = MagicMock()
            role1.id = uuid.uuid4()
            role1.name = "editor"
            role1.permissions = ["read", "write"]

            db = AsyncMock()
            scalars_mock = MagicMock()
            scalars_mock.all.return_value = [role1]
            result_mock = MagicMock()
            result_mock.scalars.return_value = scalars_mock
            db.execute.return_value = result_mock

            await settings_organisation_roles(
                _req({"session_id": "tok"}), str(tenant.id), db
            )

            mock_render.assert_called_once()
            ctx = mock_render.call_args[0][2]
            assert ctx["role"] == "owner"
            assert len(ctx["roles"]) == 1
            assert ctx["roles"][0]["name"] == "editor"
            assert ctx["roles"][0]["permissions"] == ["read", "write"]

        asyncio.run(_run())


class TestSettingsOrganisationRolesAction:
    """Tests for POST /ui/settings/organisations/{org_id}/roles."""

    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        """Redirect to login when not authenticated."""

        async def _run() -> None:
            mock_auth.return_value = None
            resp = await settings_organisation_roles_action(
                _req(),
                "some-id",
                AsyncMock(),
                action="create",
                role_name="",
                permissions="",
                role_id="",
            )
            assert resp.status_code == 302
            assert "/ui/login" in resp.headers["location"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_invalid_org_id(self, mock_auth: AsyncMock, mock_render: MagicMock) -> None:
        """Show error for invalid org ID."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            mock_render.return_value = MagicMock()

            await settings_organisation_roles_action(
                _req({"session_id": "tok"}),
                "bad-uuid",
                AsyncMock(),
                action="create",
                role_name="",
                permissions="",
                role_id="",
            )

            ctx = mock_render.call_args[0][2]
            assert "Invalid organisation ID" in ctx["error"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_not_member_shows_error(
        self, mock_auth: AsyncMock, mock_mem: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Show error when user is not a member."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            mock_mem.return_value = None
            mock_render.return_value = MagicMock()

            await settings_organisation_roles_action(
                _req({"session_id": "tok"}),
                str(uuid.uuid4()),
                AsyncMock(),
                action="create",
                role_name="",
                permissions="",
                role_id="",
            )

            ctx = mock_render.call_args[0][2]
            assert "not found" in ctx["error"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_non_admin_denied(
        self, mock_auth: AsyncMock, mock_mem: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Members without owner/admin role cannot manage roles."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="member", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            db = AsyncMock()
            scalars_mock = MagicMock()
            scalars_mock.all.return_value = []
            result_mock = MagicMock()
            result_mock.scalars.return_value = scalars_mock
            db.execute.return_value = result_mock

            await settings_organisation_roles_action(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                action="create",
                role_name="editor",
                permissions="",
                role_id="",
            )

            ctx = mock_render.call_args[0][2]
            assert "permission" in ctx["error"].lower()

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_create_empty_name_error(
        self, mock_auth: AsyncMock, mock_mem: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Creating a role with empty name shows error."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            db = AsyncMock()
            scalars_mock = MagicMock()
            scalars_mock.all.return_value = []
            result_mock = MagicMock()
            result_mock.scalars.return_value = scalars_mock
            db.execute.return_value = result_mock

            await settings_organisation_roles_action(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                action="create",
                role_name="",
                permissions="",
                role_id="",
            )

            ctx = mock_render.call_args[0][2]
            assert "required" in ctx["error"].lower()

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_create_duplicate_name_error(
        self, mock_auth: AsyncMock, mock_mem: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Creating a role with duplicate name shows error."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            existing_role = MagicMock()
            db = AsyncMock()

            call_count = 0

            def execute_side_effect(*args: object, **kwargs: object) -> MagicMock:
                nonlocal call_count
                call_count += 1
                result_mock = MagicMock()
                if call_count == 1:
                    # First call: duplicate check returns existing role
                    result_mock.scalar_one_or_none.return_value = existing_role
                else:
                    # Subsequent calls for _ctx: roles list
                    scalars_mock = MagicMock()
                    scalars_mock.all.return_value = []
                    result_mock.scalars.return_value = scalars_mock
                return result_mock

            db.execute = AsyncMock(side_effect=execute_side_effect)

            await settings_organisation_roles_action(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                action="create",
                role_name="editor",
                permissions="",
                role_id="",
            )

            ctx = mock_render.call_args[0][2]
            assert "already exists" in ctx["error"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_create_role_success(
        self, mock_auth: AsyncMock, mock_mem: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Owner can create a new custom role."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            call_count = 0

            def execute_side_effect(*args: object, **kwargs: object) -> MagicMock:
                nonlocal call_count
                call_count += 1
                result_mock = MagicMock()
                if call_count == 1:
                    # First call: uniqueness check returns None
                    result_mock.scalar_one_or_none.return_value = None
                else:
                    # Subsequent calls for _ctx: roles list
                    scalars_mock = MagicMock()
                    scalars_mock.all.return_value = []
                    result_mock.scalars.return_value = scalars_mock
                return result_mock

            db = AsyncMock()
            db.execute = AsyncMock(side_effect=execute_side_effect)

            await settings_organisation_roles_action(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                action="create",
                role_name="editor",
                permissions="read write",
            )

            db.add.assert_called_once()
            ctx = mock_render.call_args[0][2]
            assert "created" in ctx["success"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_update_role_success(
        self, mock_auth: AsyncMock, mock_mem: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Owner can update an existing custom role."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            role_obj = MagicMock()
            role_obj.name = "editor"
            rid = uuid.uuid4()

            call_count = 0

            def execute_side_effect(*args: object, **kwargs: object) -> MagicMock:
                nonlocal call_count
                call_count += 1
                result_mock = MagicMock()
                if call_count == 1:
                    # First call: find role
                    result_mock.scalar_one_or_none.return_value = role_obj
                else:
                    # Subsequent calls for _ctx: roles list
                    scalars_mock = MagicMock()
                    scalars_mock.all.return_value = []
                    result_mock.scalars.return_value = scalars_mock
                return result_mock

            db = AsyncMock()
            db.execute = AsyncMock(side_effect=execute_side_effect)

            await settings_organisation_roles_action(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                action="update",
                role_id=str(rid),
                role_name="reviewer",
                permissions="read review",
            )

            assert role_obj.name == "reviewer"
            assert role_obj.permissions == ["read", "review"]
            ctx = mock_render.call_args[0][2]
            assert "updated" in ctx["success"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_update_role_not_found(
        self, mock_auth: AsyncMock, mock_mem: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Updating a non-existent role shows error."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            call_count = 0

            def execute_side_effect(*args: object, **kwargs: object) -> MagicMock:
                nonlocal call_count
                call_count += 1
                result_mock = MagicMock()
                if call_count == 1:
                    result_mock.scalar_one_or_none.return_value = None
                else:
                    scalars_mock = MagicMock()
                    scalars_mock.all.return_value = []
                    result_mock.scalars.return_value = scalars_mock
                return result_mock

            db = AsyncMock()
            db.execute = AsyncMock(side_effect=execute_side_effect)

            await settings_organisation_roles_action(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                action="update",
                role_id=str(uuid.uuid4()),
                role_name="editor",
                permissions="",
            )

            ctx = mock_render.call_args[0][2]
            assert "not found" in ctx["error"].lower()

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_delete_role_success(
        self, mock_auth: AsyncMock, mock_mem: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Owner can delete a custom role."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            role_obj = MagicMock()
            rid = uuid.uuid4()

            call_count = 0

            def execute_side_effect(*args: object, **kwargs: object) -> MagicMock:
                nonlocal call_count
                call_count += 1
                result_mock = MagicMock()
                if call_count == 1:
                    result_mock.scalar_one_or_none.return_value = role_obj
                else:
                    scalars_mock = MagicMock()
                    scalars_mock.all.return_value = []
                    result_mock.scalars.return_value = scalars_mock
                return result_mock

            db = AsyncMock()
            db.execute = AsyncMock(side_effect=execute_side_effect)

            await settings_organisation_roles_action(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                action="delete",
                role_id=str(rid),
                role_name="",
                permissions="",
            )

            db.delete.assert_called_once_with(role_obj)
            ctx = mock_render.call_args[0][2]
            assert "deleted" in ctx["success"].lower()

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_delete_role_not_found(
        self, mock_auth: AsyncMock, mock_mem: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Deleting a non-existent role shows error."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            call_count = 0

            def execute_side_effect(*args: object, **kwargs: object) -> MagicMock:
                nonlocal call_count
                call_count += 1
                result_mock = MagicMock()
                if call_count == 1:
                    result_mock.scalar_one_or_none.return_value = None
                else:
                    scalars_mock = MagicMock()
                    scalars_mock.all.return_value = []
                    result_mock.scalars.return_value = scalars_mock
                return result_mock

            db = AsyncMock()
            db.execute = AsyncMock(side_effect=execute_side_effect)

            await settings_organisation_roles_action(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                action="delete",
                role_id=str(uuid.uuid4()),
                role_name="",
                permissions="",
            )

            ctx = mock_render.call_args[0][2]
            assert "not found" in ctx["error"].lower()

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_unknown_action_error(
        self, mock_auth: AsyncMock, mock_mem: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Unknown action shows error."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            db = AsyncMock()
            scalars_mock = MagicMock()
            scalars_mock.all.return_value = []
            result_mock = MagicMock()
            result_mock.scalars.return_value = scalars_mock
            db.execute.return_value = result_mock

            await settings_organisation_roles_action(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                action="foobar",
                role_name="",
                permissions="",
                role_id="",
            )

            ctx = mock_render.call_args[0][2]
            assert "unknown" in ctx["error"].lower()

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_update_invalid_role_id(
        self, mock_auth: AsyncMock, mock_mem: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Updating with invalid role ID shows error."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            db = AsyncMock()
            scalars_mock = MagicMock()
            scalars_mock.all.return_value = []
            result_mock = MagicMock()
            result_mock.scalars.return_value = scalars_mock
            db.execute.return_value = result_mock

            await settings_organisation_roles_action(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                action="update",
                role_id="bad-uuid",
                role_name="editor",
                permissions="",
            )

            ctx = mock_render.call_args[0][2]
            assert "invalid role id" in ctx["error"].lower()

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_delete_invalid_role_id(
        self, mock_auth: AsyncMock, mock_mem: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Deleting with invalid role ID shows error."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            db = AsyncMock()
            scalars_mock = MagicMock()
            scalars_mock.all.return_value = []
            result_mock = MagicMock()
            result_mock.scalars.return_value = scalars_mock
            db.execute.return_value = result_mock

            await settings_organisation_roles_action(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                action="delete",
                role_id="bad-uuid",
                role_name="",
                permissions="",
            )

            ctx = mock_render.call_args[0][2]
            assert "invalid role id" in ctx["error"].lower()

        asyncio.run(_run())


class TestSettingsOrganisationIdps:
    """Tests for GET /ui/settings/organisations/{org_id}/idps."""

    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        """Redirect to login when not authenticated."""

        async def _run() -> None:
            mock_auth.return_value = None
            resp = await settings_organisation_idps(_req(), "some-id", AsyncMock())
            assert resp.status_code == 302
            assert "/ui/login" in resp.headers["location"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_invalid_org_id(self, mock_auth: AsyncMock, mock_render: MagicMock) -> None:
        """Show error for invalid org ID."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            mock_render.return_value = MagicMock()

            await settings_organisation_idps(
                _req({"session_id": "tok"}), "not-a-uuid", AsyncMock()
            )

            ctx = mock_render.call_args[0][2]
            assert "Invalid organisation ID" in ctx["error"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_not_member_shows_error(
        self, mock_auth: AsyncMock, mock_mem: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Show error when user is not a member."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            mock_mem.return_value = None
            mock_render.return_value = MagicMock()

            await settings_organisation_idps(
                _req({"session_id": "tok"}), str(uuid.uuid4()), AsyncMock()
            )

            ctx = mock_render.call_args[0][2]
            assert "not found" in ctx["error"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_renders_idps_list(
        self, mock_auth: AsyncMock, mock_mem: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Render IdPs page with list of providers."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            idp1 = MagicMock()
            idp1.id = uuid.uuid4()
            idp1.name = "Acme SSO"
            idp1.provider_type = MagicMock(value="oidc")
            idp1.client_id = "acme-client"
            idp1.is_active = True

            db = AsyncMock()
            scalars_mock = MagicMock()
            scalars_mock.all.return_value = [idp1]
            result_mock = MagicMock()
            result_mock.scalars.return_value = scalars_mock
            db.execute.return_value = result_mock

            await settings_organisation_idps(
                _req({"session_id": "tok"}), str(tenant.id), db
            )

            mock_render.assert_called_once()
            ctx = mock_render.call_args[0][2]
            assert ctx["role"] == "owner"
            assert len(ctx["idps"]) == 1
            assert ctx["idps"][0]["name"] == "Acme SSO"
            assert ctx["idps"][0]["is_active"] is True

        asyncio.run(_run())


class TestSettingsOrganisationIdpsAction:
    """Tests for POST /ui/settings/organisations/{org_id}/idps."""

    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        """Redirect to login when not authenticated."""

        async def _run() -> None:
            mock_auth.return_value = None
            resp = await settings_organisation_idps_action(
                _req(),
                "some-id",
                AsyncMock(),
                action="create",
                idp_name="",
                provider_type="oidc",
                client_id="",
                discovery_url="",
                idp_id="",
            )
            assert resp.status_code == 302
            assert "/ui/login" in resp.headers["location"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_invalid_org_id(self, mock_auth: AsyncMock, mock_render: MagicMock) -> None:
        """Show error for invalid org ID."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            mock_render.return_value = MagicMock()

            await settings_organisation_idps_action(
                _req({"session_id": "tok"}),
                "bad-uuid",
                AsyncMock(),
                action="create",
                idp_name="",
                provider_type="oidc",
                client_id="",
                discovery_url="",
                idp_id="",
            )

            ctx = mock_render.call_args[0][2]
            assert "Invalid organisation ID" in ctx["error"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_non_admin_denied(
        self, mock_auth: AsyncMock, mock_mem: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Members without owner/admin role cannot manage IdPs."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="member", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            db = AsyncMock()
            scalars_mock = MagicMock()
            scalars_mock.all.return_value = []
            result_mock = MagicMock()
            result_mock.scalars.return_value = scalars_mock
            db.execute.return_value = result_mock

            await settings_organisation_idps_action(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                action="create",
                idp_name="test",
                provider_type="oidc",
                client_id="cid",
                discovery_url="",
                idp_id="",
            )

            ctx = mock_render.call_args[0][2]
            assert "permission" in ctx["error"].lower()

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_create_empty_name_error(
        self, mock_auth: AsyncMock, mock_mem: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Creating an IdP with empty name shows error."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            db = AsyncMock()
            scalars_mock = MagicMock()
            scalars_mock.all.return_value = []
            result_mock = MagicMock()
            result_mock.scalars.return_value = scalars_mock
            db.execute.return_value = result_mock

            await settings_organisation_idps_action(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                action="create",
                idp_name="",
                provider_type="oidc",
                client_id="cid",
                discovery_url="",
                idp_id="",
            )

            ctx = mock_render.call_args[0][2]
            assert "required" in ctx["error"].lower()

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_create_empty_client_id_error(
        self, mock_auth: AsyncMock, mock_mem: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Creating an IdP with empty client ID shows error."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            db = AsyncMock()
            scalars_mock = MagicMock()
            scalars_mock.all.return_value = []
            result_mock = MagicMock()
            result_mock.scalars.return_value = scalars_mock
            db.execute.return_value = result_mock

            await settings_organisation_idps_action(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                action="create",
                idp_name="Acme SSO",
                provider_type="oidc",
                client_id="",
                discovery_url="",
                idp_id="",
            )

            ctx = mock_render.call_args[0][2]
            assert "client id" in ctx["error"].lower()

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_create_invalid_type_error(
        self, mock_auth: AsyncMock, mock_mem: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Creating an IdP with invalid type shows error."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            db = AsyncMock()
            scalars_mock = MagicMock()
            scalars_mock.all.return_value = []
            result_mock = MagicMock()
            result_mock.scalars.return_value = scalars_mock
            db.execute.return_value = result_mock

            await settings_organisation_idps_action(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                action="create",
                idp_name="Acme SSO",
                provider_type="ldap",
                client_id="cid",
                discovery_url="",
                idp_id="",
            )

            ctx = mock_render.call_args[0][2]
            assert "invalid provider type" in ctx["error"].lower()

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_create_idp_success(
        self, mock_auth: AsyncMock, mock_mem: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Owner can create a new identity provider."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            db = AsyncMock()
            scalars_mock = MagicMock()
            scalars_mock.all.return_value = []
            result_mock = MagicMock()
            result_mock.scalars.return_value = scalars_mock
            db.execute.return_value = result_mock

            await settings_organisation_idps_action(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                action="create",
                idp_name="Acme SSO",
                provider_type="oidc",
                client_id="acme-client",
                discovery_url="https://sso.acme.com/.well-known/openid-configuration",
                idp_id="",
            )

            db.add.assert_called_once()
            ctx = mock_render.call_args[0][2]
            assert "created" in ctx["success"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_toggle_idp_success(
        self, mock_auth: AsyncMock, mock_mem: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Owner can toggle an IdP active/inactive."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            idp_obj = MagicMock()
            idp_obj.is_active = True
            idp_obj.name = "Acme SSO"

            call_count = 0

            def execute_side_effect(*args: object, **kwargs: object) -> MagicMock:
                nonlocal call_count
                call_count += 1
                result_mock = MagicMock()
                if call_count == 1:
                    result_mock.scalar_one_or_none.return_value = idp_obj
                else:
                    scalars_mock = MagicMock()
                    scalars_mock.all.return_value = []
                    result_mock.scalars.return_value = scalars_mock
                return result_mock

            db = AsyncMock()
            db.execute = AsyncMock(side_effect=execute_side_effect)

            await settings_organisation_idps_action(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                action="toggle",
                idp_id=str(uuid.uuid4()),
                idp_name="",
                provider_type="oidc",
                client_id="",
                discovery_url="",
            )

            assert idp_obj.is_active is False
            ctx = mock_render.call_args[0][2]
            assert "disabled" in ctx["success"]

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_toggle_idp_not_found(
        self, mock_auth: AsyncMock, mock_mem: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Toggling a non-existent IdP shows error."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            call_count = 0

            def execute_side_effect(*args: object, **kwargs: object) -> MagicMock:
                nonlocal call_count
                call_count += 1
                result_mock = MagicMock()
                if call_count == 1:
                    result_mock.scalar_one_or_none.return_value = None
                else:
                    scalars_mock = MagicMock()
                    scalars_mock.all.return_value = []
                    result_mock.scalars.return_value = scalars_mock
                return result_mock

            db = AsyncMock()
            db.execute = AsyncMock(side_effect=execute_side_effect)

            await settings_organisation_idps_action(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                action="toggle",
                idp_id=str(uuid.uuid4()),
                idp_name="",
                provider_type="oidc",
                client_id="",
                discovery_url="",
            )

            ctx = mock_render.call_args[0][2]
            assert "not found" in ctx["error"].lower()

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_delete_idp_success(
        self, mock_auth: AsyncMock, mock_mem: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Owner can delete an IdP."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            idp_obj = MagicMock()

            call_count = 0

            def execute_side_effect(*args: object, **kwargs: object) -> MagicMock:
                nonlocal call_count
                call_count += 1
                result_mock = MagicMock()
                if call_count == 1:
                    result_mock.scalar_one_or_none.return_value = idp_obj
                else:
                    scalars_mock = MagicMock()
                    scalars_mock.all.return_value = []
                    result_mock.scalars.return_value = scalars_mock
                return result_mock

            db = AsyncMock()
            db.execute = AsyncMock(side_effect=execute_side_effect)

            await settings_organisation_idps_action(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                action="delete",
                idp_id=str(uuid.uuid4()),
                idp_name="",
                provider_type="oidc",
                client_id="",
                discovery_url="",
            )

            db.delete.assert_called_once_with(idp_obj)
            ctx = mock_render.call_args[0][2]
            assert "deleted" in ctx["success"].lower()

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_delete_idp_not_found(
        self, mock_auth: AsyncMock, mock_mem: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Deleting a non-existent IdP shows error."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            call_count = 0

            def execute_side_effect(*args: object, **kwargs: object) -> MagicMock:
                nonlocal call_count
                call_count += 1
                result_mock = MagicMock()
                if call_count == 1:
                    result_mock.scalar_one_or_none.return_value = None
                else:
                    scalars_mock = MagicMock()
                    scalars_mock.all.return_value = []
                    result_mock.scalars.return_value = scalars_mock
                return result_mock

            db = AsyncMock()
            db.execute = AsyncMock(side_effect=execute_side_effect)

            await settings_organisation_idps_action(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                action="delete",
                idp_id=str(uuid.uuid4()),
                idp_name="",
                provider_type="oidc",
                client_id="",
                discovery_url="",
            )

            ctx = mock_render.call_args[0][2]
            assert "not found" in ctx["error"].lower()

        asyncio.run(_run())

    @patch("shomer.routes.organisation_settings_ui._render")
    @patch("shomer.routes.organisation_settings_ui._get_membership")
    @patch("shomer.routes.organisation_settings_ui._get_session_user")
    def test_unknown_action_error(
        self, mock_auth: AsyncMock, mock_mem: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Unknown action shows error."""

        async def _run() -> None:
            user = _mock_user()
            mock_auth.return_value = (MagicMock(), user)
            tenant = _mock_tenant()
            membership = MagicMock(role="owner", tenant=tenant)
            mock_mem.return_value = (membership, tenant)
            mock_render.return_value = MagicMock()

            db = AsyncMock()
            scalars_mock = MagicMock()
            scalars_mock.all.return_value = []
            result_mock = MagicMock()
            result_mock.scalars.return_value = scalars_mock
            db.execute.return_value = result_mock

            await settings_organisation_idps_action(
                _req({"session_id": "tok"}),
                str(tenant.id),
                db,
                action="foobar",
                idp_name="",
                provider_type="oidc",
                client_id="",
                discovery_url="",
                idp_id="",
            )

            ctx = mock_render.call_args[0][2]
            assert "unknown" in ctx["error"].lower()

        asyncio.run(_run())

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for user settings UI routes."""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from shomer.routes.settings_ui import (
    _get_session_user,
    settings_emails,
    settings_index,
    settings_profile,
    settings_profile_update,
    settings_security,
)


def _req(cookies: dict[str, str] | None = None) -> MagicMock:
    cookie_data = cookies or {}
    r = MagicMock()
    r.cookies = MagicMock()
    r.cookies.get = lambda k, d=None: cookie_data.get(k, d)
    return r


def _mock_user() -> MagicMock:
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


class TestGetSessionUser:
    """Tests for _get_session_user()."""

    def test_no_cookie_returns_none(self) -> None:
        async def _run() -> None:
            result = await _get_session_user(_req(), AsyncMock())
            assert result is None

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui.SessionService")
    def test_invalid_session_returns_none(self, mock_cls: MagicMock) -> None:
        async def _run() -> None:
            mock_svc = AsyncMock()
            mock_svc.validate.return_value = None
            mock_cls.return_value = mock_svc
            result = await _get_session_user(_req({"session_id": "bad"}), AsyncMock())
            assert result is None

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui.SessionService")
    def test_valid_session_returns_tuple(self, mock_cls: MagicMock) -> None:
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


class TestSettingsProfile:
    """Tests for GET /ui/settings/profile."""

    @patch("shomer.routes.settings_ui._get_session_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        async def _run() -> None:
            mock_auth.return_value = None
            resp = await settings_profile(_req(), AsyncMock())
            assert resp.status_code == 302
            assert "/ui/login" in resp.headers["location"]

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_authenticated_renders_page(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        async def _run() -> None:
            mock_user = _mock_user()
            mock_auth.return_value = (MagicMock(), mock_user)
            mock_render.return_value = "html"
            await settings_profile(_req({"session_id": "tok"}), AsyncMock())
            mock_render.assert_called_once()
            ctx = mock_render.call_args[0][2]
            assert ctx["section"] == "profile"
            assert ctx["user"] is mock_user

        asyncio.run(_run())


class TestSettingsEmails:
    """Tests for GET /ui/settings/emails."""

    @patch("shomer.routes.settings_ui._get_session_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        async def _run() -> None:
            mock_auth.return_value = None
            resp = await settings_emails(_req(), AsyncMock())
            assert resp.status_code == 302

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_authenticated_renders_page(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        async def _run() -> None:
            mock_user = _mock_user()
            mock_auth.return_value = (MagicMock(), mock_user)
            mock_render.return_value = "html"
            await settings_emails(_req({"session_id": "tok"}), AsyncMock())
            ctx = mock_render.call_args[0][2]
            assert ctx["section"] == "emails"
            assert len(ctx["emails"]) == 1

        asyncio.run(_run())


class TestSettingsSecurity:
    """Tests for GET /ui/settings/security."""

    @patch("shomer.routes.settings_ui._get_session_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        async def _run() -> None:
            mock_auth.return_value = None
            resp = await settings_security(_req(), AsyncMock())
            assert resp.status_code == 302

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_authenticated_renders_page(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        async def _run() -> None:
            mock_user = _mock_user()
            mock_session = MagicMock()
            mock_auth.return_value = (mock_session, mock_user)

            count_result = MagicMock()
            count_result.scalar.return_value = 2
            mfa_result = MagicMock()
            mfa_result.scalar_one_or_none.return_value = None

            db = AsyncMock()
            db.execute.side_effect = [count_result, mfa_result]

            mock_render.return_value = "html"
            await settings_security(_req({"session_id": "tok"}), db)
            ctx = mock_render.call_args[0][2]
            assert ctx["section"] == "security"
            assert ctx["active_sessions"] == 2
            assert ctx["mfa_enabled"] is False
            assert ctx["mfa_methods"] == []

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_mfa_enabled_shows_in_context(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        async def _run() -> None:
            mock_user = _mock_user()
            mock_session = MagicMock()
            mock_auth.return_value = (mock_session, mock_user)

            count_result = MagicMock()
            count_result.scalar.return_value = 1
            mock_mfa = MagicMock()
            mock_mfa.is_enabled = True
            mock_mfa.methods = ["totp", "backup"]
            mfa_result = MagicMock()
            mfa_result.scalar_one_or_none.return_value = mock_mfa

            db = AsyncMock()
            db.execute.side_effect = [count_result, mfa_result]

            mock_render.return_value = "html"
            await settings_security(_req({"session_id": "tok"}), db)
            ctx = mock_render.call_args[0][2]
            assert ctx["mfa_enabled"] is True
            assert "totp" in ctx["mfa_methods"]

        asyncio.run(_run())


class TestSettingsProfileUpdate:
    """Tests for POST /ui/settings/profile."""

    @patch("shomer.routes.settings_ui._get_session_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        """POST without session redirects to login."""

        async def _run() -> None:
            mock_auth.return_value = None
            resp = await settings_profile_update(_req(), AsyncMock())
            assert resp.status_code == 302
            assert "/ui/login" in resp.headers["location"]

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_saves_profile_fields(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """POST with valid data updates profile and shows success."""

        async def _run() -> None:
            mock_user = _mock_user()
            mock_profile = MagicMock()
            mock_user.profile = mock_profile
            mock_auth.return_value = (MagicMock(), mock_user)
            mock_render.return_value = "html"

            db = AsyncMock()
            await settings_profile_update(
                _req({"session_id": "tok"}),
                db,
                nickname="Jo",
                given_name="John",
                family_name="Doe",
                middle_name="M",
                preferred_username="johnd",
                gender="male",
                birthdate="1990-01-15",
                zoneinfo="Europe/Paris",
                locale="fr-FR",
                phone_number="+33612345678",
                website="https://example.com",
                profile_url="https://linkedin.com/in/john",
                picture_url="https://pic.example.com/me.jpg",
                address_street="123 Main St",
                address_locality="Paris",
                address_region="IDF",
                address_postal_code="75001",
                address_country="France",
            )

            # Verify profile was updated
            assert mock_profile.nickname == "Jo"
            assert mock_profile.given_name == "John"
            assert mock_profile.family_name == "Doe"
            assert mock_profile.middle_name == "M"
            assert mock_profile.address_street == "123 Main St"
            assert mock_profile.phone_number == "+33612345678"

            db.flush.assert_awaited_once()

            ctx = mock_render.call_args[0][2]
            assert ctx["success"] == "Profile updated successfully."
            assert ctx["error"] is None

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui.UserProfile")
    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_creates_profile_if_none(
        self, mock_auth: AsyncMock, mock_render: MagicMock, mock_up_cls: MagicMock
    ) -> None:
        """POST creates a new UserProfile when user has none."""

        async def _run() -> None:
            mock_user = _mock_user()
            mock_user.profile = None
            mock_auth.return_value = (MagicMock(), mock_user)
            mock_render.return_value = "html"

            new_profile = MagicMock()
            mock_up_cls.return_value = new_profile

            db = AsyncMock()
            await settings_profile_update(
                _req({"session_id": "tok"}),
                db,
                nickname="New",
            )

            db.add.assert_called_once_with(new_profile)
            db.flush.assert_awaited_once()
            assert new_profile.nickname == "New"

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_empty_fields_become_none(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Empty string form values are stored as None."""

        async def _run() -> None:
            mock_user = _mock_user()
            mock_profile = MagicMock()
            mock_user.profile = mock_profile
            mock_auth.return_value = (MagicMock(), mock_user)
            mock_render.return_value = "html"

            db = AsyncMock()
            await settings_profile_update(
                _req({"session_id": "tok"}),
                db,
                nickname="",
                gender="",
            )

            assert mock_profile.nickname is None
            assert mock_profile.gender is None

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_get_includes_email_in_context(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """GET renders profile page with primary email in context."""

        async def _run() -> None:
            mock_user = _mock_user()
            mock_auth.return_value = (MagicMock(), mock_user)
            mock_render.return_value = "html"

            await settings_profile(_req({"session_id": "tok"}), AsyncMock())
            ctx = mock_render.call_args[0][2]
            assert ctx["email"] == "test@example.com"
            assert ctx["success"] is None
            assert ctx["error"] is None

        asyncio.run(_run())


class TestSettingsIndex:
    """Tests for GET /ui/settings (index/dashboard)."""

    @patch("shomer.routes.settings_ui._get_session_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        """Unauthenticated request redirects to login."""

        async def _run() -> None:
            mock_auth.return_value = None
            resp = await settings_index(_req(), AsyncMock())
            assert resp.status_code == 302
            assert "/ui/login" in resp.headers["location"]

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_authenticated_renders_overview(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Authenticated request renders the index page with all stats."""

        async def _run() -> None:
            mock_user = _mock_user()
            # Profile with some fields filled
            mock_profile = MagicMock()
            mock_profile.nickname = "Jo"
            mock_profile.given_name = "John"
            mock_profile.family_name = "Doe"
            mock_profile.picture_url = None
            mock_profile.phone_number = None
            mock_profile.locale = None
            mock_profile.zoneinfo = None
            mock_user.profile = mock_profile
            mock_auth.return_value = (MagicMock(), mock_user)

            # db.execute returns: mfa_result, sessions_result, pat_result
            mfa_result = MagicMock()
            mfa_result.scalar_one_or_none.return_value = None
            sessions_result = MagicMock()
            sessions_result.scalar.return_value = 3
            pat_result = MagicMock()
            pat_result.scalar.return_value = 2

            db = AsyncMock()
            db.execute.side_effect = [mfa_result, sessions_result, pat_result]

            mock_render.return_value = "html"
            await settings_index(_req({"session_id": "tok"}), db)
            ctx = mock_render.call_args[0][2]
            assert ctx["section"] == "overview"
            assert ctx["completeness"] == 43  # 3/7 = 42.86 → 43
            assert ctx["has_verified_email"] is True
            assert ctx["mfa_enabled"] is False
            assert ctx["active_sessions"] == 3
            assert ctx["active_pats"] == 2

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_no_profile_shows_zero_completeness(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """User with no profile shows 0% completeness."""

        async def _run() -> None:
            mock_user = _mock_user()
            mock_user.profile = None
            # Unverified email
            mock_user.emails[0].is_verified = False
            mock_auth.return_value = (MagicMock(), mock_user)

            mfa_result = MagicMock()
            mfa_result.scalar_one_or_none.return_value = None
            sessions_result = MagicMock()
            sessions_result.scalar.return_value = 0
            pat_result = MagicMock()
            pat_result.scalar.return_value = 0

            db = AsyncMock()
            db.execute.side_effect = [mfa_result, sessions_result, pat_result]

            mock_render.return_value = "html"
            await settings_index(_req({"session_id": "tok"}), db)
            ctx = mock_render.call_args[0][2]
            assert ctx["completeness"] == 0
            assert ctx["has_verified_email"] is False
            assert ctx["active_sessions"] == 0
            assert ctx["active_pats"] == 0

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_mfa_enabled_shows_in_context(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """MFA enabled status is reflected in context."""

        async def _run() -> None:
            mock_user = _mock_user()
            mock_user.profile = None
            mock_auth.return_value = (MagicMock(), mock_user)

            mock_mfa = MagicMock()
            mock_mfa.is_enabled = True
            mfa_result = MagicMock()
            mfa_result.scalar_one_or_none.return_value = mock_mfa
            sessions_result = MagicMock()
            sessions_result.scalar.return_value = 1
            pat_result = MagicMock()
            pat_result.scalar.return_value = 0

            db = AsyncMock()
            db.execute.side_effect = [mfa_result, sessions_result, pat_result]

            mock_render.return_value = "html"
            await settings_index(_req({"session_id": "tok"}), db)
            ctx = mock_render.call_args[0][2]
            assert ctx["mfa_enabled"] is True

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_full_profile_shows_100_completeness(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """User with all profile fields filled shows 100% completeness."""

        async def _run() -> None:
            mock_user = _mock_user()
            mock_profile = MagicMock()
            mock_profile.nickname = "Jo"
            mock_profile.given_name = "John"
            mock_profile.family_name = "Doe"
            mock_profile.picture_url = "https://example.com/pic.jpg"
            mock_profile.phone_number = "+33612345678"
            mock_profile.locale = "fr-FR"
            mock_profile.zoneinfo = "Europe/Paris"
            mock_user.profile = mock_profile
            mock_auth.return_value = (MagicMock(), mock_user)

            mfa_result = MagicMock()
            mfa_result.scalar_one_or_none.return_value = None
            sessions_result = MagicMock()
            sessions_result.scalar.return_value = 1
            pat_result = MagicMock()
            pat_result.scalar.return_value = 0

            db = AsyncMock()
            db.execute.side_effect = [mfa_result, sessions_result, pat_result]

            mock_render.return_value = "html"
            await settings_index(_req({"session_id": "tok"}), db)
            ctx = mock_render.call_args[0][2]
            assert ctx["completeness"] == 100

        asyncio.run(_run())

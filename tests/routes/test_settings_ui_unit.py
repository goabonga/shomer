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
    settings_emails_post,
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

    @patch("shomer.routes.settings_ui.SessionService")
    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_authenticated_renders_page(
        self, mock_auth: AsyncMock, mock_render: MagicMock, mock_svc_cls: MagicMock
    ) -> None:
        async def _run() -> None:
            mock_user = _mock_user()
            mock_session = MagicMock()
            mock_auth.return_value = (mock_session, mock_user)

            mock_svc = AsyncMock()
            mock_svc.list_active.return_value = [MagicMock(), MagicMock()]
            mock_svc_cls.return_value = mock_svc

            mfa_result = MagicMock()
            mfa_result.scalar_one_or_none.return_value = None

            db = AsyncMock()
            db.execute.return_value = mfa_result

            mock_render.return_value = "html"
            await settings_security(_req({"session_id": "tok"}), db)
            ctx = mock_render.call_args[0][2]
            assert ctx["section"] == "security"
            assert ctx["active_sessions"] == 2
            assert ctx["mfa_enabled"] is False
            assert ctx["mfa_methods"] == []

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui.SessionService")
    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_mfa_enabled_shows_in_context(
        self, mock_auth: AsyncMock, mock_render: MagicMock, mock_svc_cls: MagicMock
    ) -> None:
        async def _run() -> None:
            mock_user = _mock_user()
            mock_session = MagicMock()
            mock_auth.return_value = (mock_session, mock_user)

            mock_svc = AsyncMock()
            mock_svc.list_active.return_value = [MagicMock()]
            mock_svc_cls.return_value = mock_svc

            mock_mfa = MagicMock()
            mock_mfa.is_enabled = True
            mock_mfa.methods = ["totp", "backup"]
            mfa_result = MagicMock()
            mfa_result.scalar_one_or_none.return_value = mock_mfa

            db = AsyncMock()
            db.execute.return_value = mfa_result

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


class TestSettingsEmailsAdd:
    """Tests for POST /ui/settings/emails (add email)."""

    @patch("shomer.routes.settings_ui._get_session_user")
    def test_unauthenticated_redirects(self, mock_auth: AsyncMock) -> None:
        """POST without session redirects to login."""

        async def _run() -> None:
            mock_auth.return_value = None
            resp = await settings_emails_post(_req(), AsyncMock())
            assert resp.status_code == 302
            assert "/ui/login" in resp.headers["location"]

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_empty_email_shows_error(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """POST with blank email shows validation error."""

        async def _run() -> None:
            mock_user = _mock_user()
            mock_auth.return_value = (MagicMock(), mock_user)
            mock_render.return_value = "html"

            db = AsyncMock()
            # Re-load query
            reload_result = MagicMock()
            reload_result.scalar_one_or_none.return_value = mock_user
            db.execute.return_value = reload_result

            await settings_emails_post(
                _req({"session_id": "tok"}), db, action="add", email=""
            )
            ctx = mock_render.call_args[0][2]
            assert ctx["error"] == "Email address is required."
            assert ctx["success"] is None

        asyncio.run(_run())

    @patch("shomer.tasks.email.send_email_task")
    @patch("shomer.services.auth_service.AuthService")
    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_add_email_success(
        self,
        mock_auth: AsyncMock,
        mock_render: MagicMock,
        mock_auth_svc_cls: MagicMock,
        mock_send_task: MagicMock,
    ) -> None:
        """POST with valid email adds it and shows success."""

        async def _run() -> None:
            mock_user = _mock_user()
            mock_auth.return_value = (MagicMock(), mock_user)
            mock_render.return_value = "html"

            mock_auth_svc = MagicMock()
            mock_auth_svc._generate_code.return_value = "123456"
            mock_auth_svc_cls.return_value = mock_auth_svc

            db = AsyncMock()
            # First call: check existing email (not found)
            existing_result = MagicMock()
            existing_result.scalar_one_or_none.return_value = None
            # Second call: re-load user
            reload_result = MagicMock()
            reload_result.scalar_one_or_none.return_value = mock_user
            db.execute.side_effect = [existing_result, reload_result]

            await settings_emails_post(
                _req({"session_id": "tok"}), db, action="add", email="new@example.com"
            )

            # Verify email was added
            db.add.assert_called()
            db.flush.assert_awaited()

            ctx = mock_render.call_args[0][2]
            assert ctx["success"] == "Email added. Check your inbox for verification."
            assert ctx["error"] is None

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_duplicate_email_shows_error(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """POST with already-registered email shows conflict error."""

        async def _run() -> None:
            mock_user = _mock_user()
            mock_auth.return_value = (MagicMock(), mock_user)
            mock_render.return_value = "html"

            db = AsyncMock()
            # First call: check existing email (found)
            existing_result = MagicMock()
            existing_result.scalar_one_or_none.return_value = MagicMock()
            # Second call: re-load user
            reload_result = MagicMock()
            reload_result.scalar_one_or_none.return_value = mock_user
            db.execute.side_effect = [existing_result, reload_result]

            await settings_emails_post(
                _req({"session_id": "tok"}),
                db,
                action="add",
                email="taken@example.com",
            )

            ctx = mock_render.call_args[0][2]
            assert ctx["error"] == "Email already registered."
            assert ctx["success"] is None

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_get_emails_includes_success_error_none(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """GET emails page passes success=None and error=None in context."""

        async def _run() -> None:
            mock_user = _mock_user()
            mock_auth.return_value = (MagicMock(), mock_user)
            mock_render.return_value = "html"

            await settings_emails(_req({"session_id": "tok"}), AsyncMock())
            ctx = mock_render.call_args[0][2]
            assert ctx["success"] is None
            assert ctx["error"] is None

        asyncio.run(_run())


class TestSettingsEmailsRemove:
    """Tests for POST /ui/settings/emails action=remove."""

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_remove_email_success(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Remove a non-primary email shows success."""

        async def _run() -> None:
            mock_user = _mock_user()
            mock_auth.return_value = (MagicMock(), mock_user)
            mock_render.return_value = "html"

            email_record = MagicMock()
            email_record.is_primary = False

            db = AsyncMock()
            # First call: find email by id
            find_result = MagicMock()
            find_result.scalar_one_or_none.return_value = email_record
            # Second call: re-load user
            reload_result = MagicMock()
            reload_result.scalar_one_or_none.return_value = mock_user
            db.execute.side_effect = [find_result, reload_result]

            eid = str(uuid.uuid4())
            await settings_emails_post(
                _req({"session_id": "tok"}), db, action="remove", email_id=eid
            )

            db.delete.assert_awaited_once_with(email_record)
            ctx = mock_render.call_args[0][2]
            assert ctx["success"] == "Email removed."
            assert ctx["error"] is None

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_remove_primary_email_shows_error(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Removing primary email shows error."""

        async def _run() -> None:
            mock_user = _mock_user()
            mock_auth.return_value = (MagicMock(), mock_user)
            mock_render.return_value = "html"

            email_record = MagicMock()
            email_record.is_primary = True

            db = AsyncMock()
            find_result = MagicMock()
            find_result.scalar_one_or_none.return_value = email_record
            reload_result = MagicMock()
            reload_result.scalar_one_or_none.return_value = mock_user
            db.execute.side_effect = [find_result, reload_result]

            eid = str(uuid.uuid4())
            await settings_emails_post(
                _req({"session_id": "tok"}), db, action="remove", email_id=eid
            )

            db.delete.assert_not_awaited()
            ctx = mock_render.call_args[0][2]
            assert ctx["error"] == "Cannot delete primary email."

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_remove_nonexistent_email_shows_error(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Removing a non-existent email shows error."""

        async def _run() -> None:
            mock_user = _mock_user()
            mock_auth.return_value = (MagicMock(), mock_user)
            mock_render.return_value = "html"

            db = AsyncMock()
            find_result = MagicMock()
            find_result.scalar_one_or_none.return_value = None
            reload_result = MagicMock()
            reload_result.scalar_one_or_none.return_value = mock_user
            db.execute.side_effect = [find_result, reload_result]

            eid = str(uuid.uuid4())
            await settings_emails_post(
                _req({"session_id": "tok"}), db, action="remove", email_id=eid
            )

            ctx = mock_render.call_args[0][2]
            assert ctx["error"] == "Email not found."

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_remove_invalid_uuid_shows_error(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Removing with invalid UUID shows error."""

        async def _run() -> None:
            mock_user = _mock_user()
            mock_auth.return_value = (MagicMock(), mock_user)
            mock_render.return_value = "html"

            db = AsyncMock()
            reload_result = MagicMock()
            reload_result.scalar_one_or_none.return_value = mock_user
            db.execute.return_value = reload_result

            await settings_emails_post(
                _req({"session_id": "tok"}),
                db,
                action="remove",
                email_id="not-a-uuid",
            )

            ctx = mock_render.call_args[0][2]
            assert ctx["error"] == "Invalid email ID."

        asyncio.run(_run())


class TestSettingsEmailsVerify:
    """Tests for POST /ui/settings/emails action=verify."""

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_verify_empty_code_shows_error(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Verify with empty code shows validation error."""

        async def _run() -> None:
            mock_user = _mock_user()
            mock_auth.return_value = (MagicMock(), mock_user)
            mock_render.return_value = "html"

            db = AsyncMock()
            reload_result = MagicMock()
            reload_result.scalar_one_or_none.return_value = mock_user
            db.execute.return_value = reload_result

            await settings_emails_post(
                _req({"session_id": "tok"}),
                db,
                action="verify",
                email_id=str(uuid.uuid4()),
                code="",
            )

            ctx = mock_render.call_args[0][2]
            assert ctx["error"] == "Verification code is required."

        asyncio.run(_run())

    @patch("shomer.services.auth_service.AuthService.verify_email")
    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_verify_email_success(
        self,
        mock_auth: AsyncMock,
        mock_render: MagicMock,
        mock_verify: AsyncMock,
    ) -> None:
        """Verify with valid code succeeds."""

        async def _run() -> None:
            mock_user = _mock_user()
            mock_auth.return_value = (MagicMock(), mock_user)
            mock_render.return_value = "html"

            target_email = MagicMock()
            target_email.is_verified = False
            target_email.email = "new@example.com"

            db = AsyncMock()
            # First call: find email by id
            find_result = MagicMock()
            find_result.scalar_one_or_none.return_value = target_email
            # Second call: re-load user
            reload_result = MagicMock()
            reload_result.scalar_one_or_none.return_value = mock_user
            db.execute.side_effect = [find_result, reload_result]

            mock_verify.return_value = None

            await settings_emails_post(
                _req({"session_id": "tok"}),
                db,
                action="verify",
                email_id=str(uuid.uuid4()),
                code="123456",
            )

            mock_verify.assert_awaited_once_with(email="new@example.com", code="123456")
            ctx = mock_render.call_args[0][2]
            assert ctx["success"] == "Email verified successfully."
            assert ctx["error"] is None

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_verify_invalid_code_shows_error(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Verify with wrong code shows error."""

        async def _run() -> None:
            from shomer.services.auth_service import InvalidCodeError

            mock_user = _mock_user()
            mock_auth.return_value = (MagicMock(), mock_user)
            mock_render.return_value = "html"

            target_email = MagicMock()
            target_email.is_verified = False
            target_email.email = "new@example.com"

            db = AsyncMock()
            find_result = MagicMock()
            find_result.scalar_one_or_none.return_value = target_email
            reload_result = MagicMock()
            reload_result.scalar_one_or_none.return_value = mock_user
            db.execute.side_effect = [find_result, reload_result]

            with patch(
                "shomer.services.auth_service.AuthService.verify_email",
                side_effect=InvalidCodeError("bad"),
            ):
                await settings_emails_post(
                    _req({"session_id": "tok"}),
                    db,
                    action="verify",
                    email_id=str(uuid.uuid4()),
                    code="000000",
                )

            ctx = mock_render.call_args[0][2]
            assert ctx["error"] == "Invalid or expired verification code."

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_verify_already_verified_shows_error(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Verify an already-verified email shows error."""

        async def _run() -> None:
            mock_user = _mock_user()
            mock_auth.return_value = (MagicMock(), mock_user)
            mock_render.return_value = "html"

            target_email = MagicMock()
            target_email.is_verified = True

            db = AsyncMock()
            find_result = MagicMock()
            find_result.scalar_one_or_none.return_value = target_email
            reload_result = MagicMock()
            reload_result.scalar_one_or_none.return_value = mock_user
            db.execute.side_effect = [find_result, reload_result]

            await settings_emails_post(
                _req({"session_id": "tok"}),
                db,
                action="verify",
                email_id=str(uuid.uuid4()),
                code="123456",
            )

            ctx = mock_render.call_args[0][2]
            assert ctx["error"] == "Email is already verified."

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_verify_nonexistent_email_shows_error(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Verify a non-existent email shows error."""

        async def _run() -> None:
            mock_user = _mock_user()
            mock_auth.return_value = (MagicMock(), mock_user)
            mock_render.return_value = "html"

            db = AsyncMock()
            find_result = MagicMock()
            find_result.scalar_one_or_none.return_value = None
            reload_result = MagicMock()
            reload_result.scalar_one_or_none.return_value = mock_user
            db.execute.side_effect = [find_result, reload_result]

            await settings_emails_post(
                _req({"session_id": "tok"}),
                db,
                action="verify",
                email_id=str(uuid.uuid4()),
                code="123456",
            )

            ctx = mock_render.call_args[0][2]
            assert ctx["error"] == "Email not found."

        asyncio.run(_run())


class TestSettingsEmailsResend:
    """Tests for POST /ui/settings/emails action=resend."""

    @patch("shomer.tasks.email.send_email_task")
    @patch("shomer.services.auth_service.AuthService")
    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_resend_success(
        self,
        mock_auth: AsyncMock,
        mock_render: MagicMock,
        mock_auth_svc_cls: MagicMock,
        mock_send_task: MagicMock,
    ) -> None:
        """Resend verification for unverified email shows success."""

        async def _run() -> None:
            mock_user = _mock_user()
            mock_auth.return_value = (MagicMock(), mock_user)
            mock_render.return_value = "html"

            mock_auth_svc = MagicMock()
            mock_auth_svc._generate_code.return_value = "654321"
            mock_auth_svc_cls.return_value = mock_auth_svc

            target_email = MagicMock()
            target_email.is_verified = False
            target_email.email = "unverified@example.com"

            db = AsyncMock()
            find_result = MagicMock()
            find_result.scalar_one_or_none.return_value = target_email
            reload_result = MagicMock()
            reload_result.scalar_one_or_none.return_value = mock_user
            db.execute.side_effect = [find_result, reload_result]

            await settings_emails_post(
                _req({"session_id": "tok"}),
                db,
                action="resend",
                email_id=str(uuid.uuid4()),
            )

            db.add.assert_called()
            db.flush.assert_awaited()
            ctx = mock_render.call_args[0][2]
            assert ctx["success"] == "Verification email resent."
            assert ctx["error"] is None

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_resend_already_verified_shows_error(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Resend for already-verified email shows error."""

        async def _run() -> None:
            mock_user = _mock_user()
            mock_auth.return_value = (MagicMock(), mock_user)
            mock_render.return_value = "html"

            target_email = MagicMock()
            target_email.is_verified = True

            db = AsyncMock()
            find_result = MagicMock()
            find_result.scalar_one_or_none.return_value = target_email
            reload_result = MagicMock()
            reload_result.scalar_one_or_none.return_value = mock_user
            db.execute.side_effect = [find_result, reload_result]

            await settings_emails_post(
                _req({"session_id": "tok"}),
                db,
                action="resend",
                email_id=str(uuid.uuid4()),
            )

            ctx = mock_render.call_args[0][2]
            assert ctx["error"] == "Email is already verified."

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_resend_nonexistent_email_shows_error(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Resend for non-existent email shows error."""

        async def _run() -> None:
            mock_user = _mock_user()
            mock_auth.return_value = (MagicMock(), mock_user)
            mock_render.return_value = "html"

            db = AsyncMock()
            find_result = MagicMock()
            find_result.scalar_one_or_none.return_value = None
            reload_result = MagicMock()
            reload_result.scalar_one_or_none.return_value = mock_user
            db.execute.side_effect = [find_result, reload_result]

            await settings_emails_post(
                _req({"session_id": "tok"}),
                db,
                action="resend",
                email_id=str(uuid.uuid4()),
            )

            ctx = mock_render.call_args[0][2]
            assert ctx["error"] == "Email not found."

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_resend_invalid_uuid_shows_error(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Resend with invalid UUID shows error."""

        async def _run() -> None:
            mock_user = _mock_user()
            mock_auth.return_value = (MagicMock(), mock_user)
            mock_render.return_value = "html"

            db = AsyncMock()
            reload_result = MagicMock()
            reload_result.scalar_one_or_none.return_value = mock_user
            db.execute.return_value = reload_result

            await settings_emails_post(
                _req({"session_id": "tok"}),
                db,
                action="resend",
                email_id="bad-uuid",
            )

            ctx = mock_render.call_args[0][2]
            assert ctx["error"] == "Invalid email ID."

        asyncio.run(_run())


class TestSettingsEmailsSetPrimary:
    """Tests for POST /ui/settings/emails action=set_primary."""

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_set_primary_success(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Set primary on a verified email succeeds."""

        async def _run() -> None:
            mock_user = _mock_user()
            mock_auth.return_value = (MagicMock(), mock_user)
            mock_render.return_value = "html"

            target_email = MagicMock()
            target_email.is_verified = True

            eid = uuid.uuid4()
            old_primary = MagicMock()
            old_primary.id = uuid.uuid4()
            old_primary.is_primary = True
            new_primary = MagicMock()
            new_primary.id = eid
            new_primary.is_primary = False

            scalars_mock = MagicMock()
            scalars_mock.all.return_value = [old_primary, new_primary]

            db = AsyncMock()
            # First: find target email
            find_result = MagicMock()
            find_result.scalar_one_or_none.return_value = target_email
            # Second: get all emails for user
            all_result = MagicMock()
            all_result.scalars.return_value = scalars_mock
            # Third: re-load user
            reload_result = MagicMock()
            reload_result.scalar_one_or_none.return_value = mock_user
            db.execute.side_effect = [find_result, all_result, reload_result]

            await settings_emails_post(
                _req({"session_id": "tok"}),
                db,
                action="set_primary",
                email_id=str(eid),
            )

            db.flush.assert_awaited()
            assert old_primary.is_primary is False
            assert new_primary.is_primary is True
            ctx = mock_render.call_args[0][2]
            assert ctx["success"] == "Primary email updated."
            assert ctx["error"] is None

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_set_primary_unverified_shows_error(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Set primary on unverified email shows error."""

        async def _run() -> None:
            mock_user = _mock_user()
            mock_auth.return_value = (MagicMock(), mock_user)
            mock_render.return_value = "html"

            target_email = MagicMock()
            target_email.is_verified = False

            db = AsyncMock()
            find_result = MagicMock()
            find_result.scalar_one_or_none.return_value = target_email
            reload_result = MagicMock()
            reload_result.scalar_one_or_none.return_value = mock_user
            db.execute.side_effect = [find_result, reload_result]

            await settings_emails_post(
                _req({"session_id": "tok"}),
                db,
                action="set_primary",
                email_id=str(uuid.uuid4()),
            )

            ctx = mock_render.call_args[0][2]
            assert ctx["error"] == "Cannot set unverified email as primary."

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_set_primary_nonexistent_shows_error(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Set primary on non-existent email shows error."""

        async def _run() -> None:
            mock_user = _mock_user()
            mock_auth.return_value = (MagicMock(), mock_user)
            mock_render.return_value = "html"

            db = AsyncMock()
            find_result = MagicMock()
            find_result.scalar_one_or_none.return_value = None
            reload_result = MagicMock()
            reload_result.scalar_one_or_none.return_value = mock_user
            db.execute.side_effect = [find_result, reload_result]

            await settings_emails_post(
                _req({"session_id": "tok"}),
                db,
                action="set_primary",
                email_id=str(uuid.uuid4()),
            )

            ctx = mock_render.call_args[0][2]
            assert ctx["error"] == "Email not found."

        asyncio.run(_run())

    @patch("shomer.routes.settings_ui._render")
    @patch("shomer.routes.settings_ui._get_session_user")
    def test_set_primary_invalid_uuid_shows_error(
        self, mock_auth: AsyncMock, mock_render: MagicMock
    ) -> None:
        """Set primary with invalid UUID shows error."""

        async def _run() -> None:
            mock_user = _mock_user()
            mock_auth.return_value = (MagicMock(), mock_user)
            mock_render.return_value = "html"

            db = AsyncMock()
            reload_result = MagicMock()
            reload_result.scalar_one_or_none.return_value = mock_user
            db.execute.return_value = reload_result

            await settings_emails_post(
                _req({"session_id": "tok"}),
                db,
                action="set_primary",
                email_id="bad",
            )

            ctx = mock_render.call_args[0][2]
            assert ctx["error"] == "Invalid email ID."

        asyncio.run(_run())

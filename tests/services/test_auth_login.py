# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for AuthService login method."""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from shomer.services.auth_service import (
    AuthService,
    EmailNotVerifiedError,
    InvalidCredentialsError,
)


class TestLogin:
    """Tests for AuthService.login()."""

    def test_login_success(self) -> None:
        """Successful login returns user, session, and raw token."""

        async def _run() -> None:
            db = AsyncMock()

            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()
            mock_email = MagicMock()
            mock_email.is_primary = True
            mock_email.is_verified = True
            mock_user.emails = [mock_email]

            mock_pw = MagicMock()
            mock_pw.password_hash = "$argon2id$hash"

            pw_result = MagicMock()
            pw_result.scalar_one_or_none.return_value = mock_pw
            db.execute.return_value = pw_result
            db.add = MagicMock()
            db.flush = AsyncMock()

            with (
                patch(
                    "shomer.services.auth_service.get_user_by_email",
                    new_callable=AsyncMock,
                    return_value=mock_user,
                ),
                patch(
                    "shomer.services.auth_service.verify_password",
                    return_value=True,
                ),
            ):
                svc = AuthService(db)
                user, sess, token = await svc.login(
                    email="user@example.com", password="securepassword"
                )
                assert user.id is not None
                assert sess.token_hash is not None
                assert sess.csrf_token is not None
                assert len(token) == 32

        asyncio.run(_run())

    def test_login_creates_session(self) -> None:
        """Login adds a Session object to the database."""

        async def _run() -> None:
            db = AsyncMock()

            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()
            mock_email = MagicMock()
            mock_email.is_primary = True
            mock_email.is_verified = True
            mock_user.emails = [mock_email]

            mock_pw = MagicMock()
            mock_pw.password_hash = "$argon2id$hash"

            pw_result = MagicMock()
            pw_result.scalar_one_or_none.return_value = mock_pw
            db.execute.return_value = pw_result
            db.add = MagicMock()
            db.flush = AsyncMock()

            with (
                patch(
                    "shomer.services.auth_service.get_user_by_email",
                    new_callable=AsyncMock,
                    return_value=mock_user,
                ),
                patch(
                    "shomer.services.auth_service.verify_password",
                    return_value=True,
                ),
            ):
                svc = AuthService(db)
                _, sess, _ = await svc.login(
                    email="user@example.com", password="securepassword"
                )
                db.add.assert_called_once()
                added_obj = db.add.call_args[0][0]
                assert added_obj.user_id == mock_user.id

        asyncio.run(_run())

    def test_login_stores_user_agent_and_ip(self) -> None:
        """Login stores user_agent and ip_address in the session."""

        async def _run() -> None:
            db = AsyncMock()

            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()
            mock_email = MagicMock()
            mock_email.is_primary = True
            mock_email.is_verified = True
            mock_user.emails = [mock_email]

            mock_pw = MagicMock()
            mock_pw.password_hash = "$argon2id$hash"

            pw_result = MagicMock()
            pw_result.scalar_one_or_none.return_value = mock_pw
            db.execute.return_value = pw_result
            db.add = MagicMock()
            db.flush = AsyncMock()

            with (
                patch(
                    "shomer.services.auth_service.get_user_by_email",
                    new_callable=AsyncMock,
                    return_value=mock_user,
                ),
                patch(
                    "shomer.services.auth_service.verify_password",
                    return_value=True,
                ),
            ):
                svc = AuthService(db)
                _, sess, _ = await svc.login(
                    email="user@example.com",
                    password="securepassword",
                    user_agent="Mozilla/5.0",
                    ip_address="192.168.1.1",
                )
                assert sess.user_agent == "Mozilla/5.0"
                assert sess.ip_address == "192.168.1.1"

        asyncio.run(_run())

    def test_wrong_password_raises(self) -> None:
        """Wrong password raises InvalidCredentialsError."""

        async def _run() -> None:
            db = AsyncMock()

            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()

            mock_pw = MagicMock()
            mock_pw.password_hash = "$argon2id$hash"

            pw_result = MagicMock()
            pw_result.scalar_one_or_none.return_value = mock_pw
            db.execute.return_value = pw_result

            with (
                patch(
                    "shomer.services.auth_service.get_user_by_email",
                    new_callable=AsyncMock,
                    return_value=mock_user,
                ),
                patch(
                    "shomer.services.auth_service.verify_password",
                    return_value=False,
                ),
            ):
                svc = AuthService(db)
                with pytest.raises(InvalidCredentialsError):
                    await svc.login(email="user@example.com", password="wrong")

        asyncio.run(_run())

    def test_unknown_email_raises(self) -> None:
        """Unknown email raises InvalidCredentialsError."""

        async def _run() -> None:
            db = AsyncMock()

            with (
                patch(
                    "shomer.services.auth_service.get_user_by_email",
                    new_callable=AsyncMock,
                    return_value=None,
                ),
                patch("shomer.services.auth_service.hash_password"),
            ):
                svc = AuthService(db)
                with pytest.raises(InvalidCredentialsError):
                    await svc.login(email="nobody@example.com", password="pass")

        asyncio.run(_run())

    def test_unverified_email_raises(self) -> None:
        """Unverified email raises EmailNotVerifiedError."""

        async def _run() -> None:
            db = AsyncMock()

            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()
            mock_email = MagicMock()
            mock_email.is_primary = True
            mock_email.is_verified = False
            mock_user.emails = [mock_email]

            mock_pw = MagicMock()
            mock_pw.password_hash = "$argon2id$hash"

            pw_result = MagicMock()
            pw_result.scalar_one_or_none.return_value = mock_pw
            db.execute.return_value = pw_result

            with (
                patch(
                    "shomer.services.auth_service.get_user_by_email",
                    new_callable=AsyncMock,
                    return_value=mock_user,
                ),
                patch(
                    "shomer.services.auth_service.verify_password",
                    return_value=True,
                ),
            ):
                svc = AuthService(db)
                with pytest.raises(EmailNotVerifiedError):
                    await svc.login(
                        email="unverified@example.com", password="securepassword"
                    )

        asyncio.run(_run())

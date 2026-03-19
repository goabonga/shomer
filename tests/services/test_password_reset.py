# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for AuthService password reset methods."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from shomer.services.auth_service import AuthService, InvalidResetTokenError


def _flush_sets_token(db: AsyncMock) -> None:
    """Configure db.flush to populate PasswordResetToken.token.

    The PasswordResetToken model has ``default=uuid.uuid4`` which is a
    server-side column default. Without a real DB, the ``token`` attribute
    stays ``None`` after construction. This helper makes ``flush`` set it.
    """
    original_flush = db.flush

    async def _patched_flush() -> None:
        # Find the PasswordResetToken that was added and set its token
        if db.add.call_args:
            obj = db.add.call_args[0][0]
            from shomer.models.password_reset_token import PasswordResetToken

            if isinstance(obj, PasswordResetToken) and obj.token is None:
                obj.token = uuid.uuid4()
        await original_flush()

    db.flush = AsyncMock(side_effect=_patched_flush)


class TestRequestPasswordReset:
    """Tests for AuthService.request_password_reset()."""

    def test_returns_token_for_existing_user(self) -> None:
        """Returns a UUID token for a registered email."""

        async def _run() -> None:
            db = AsyncMock()
            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()

            db.add = MagicMock()
            _flush_sets_token(db)

            with patch(
                "shomer.services.auth_service.get_user_by_email",
                new_callable=AsyncMock,
                return_value=mock_user,
            ):
                svc = AuthService(db)
                token = await svc.request_password_reset(email="user@example.com")
                assert token is not None
                assert isinstance(token, uuid.UUID)
                db.add.assert_called_once()

        asyncio.run(_run())

    def test_returns_none_for_unknown_email(self) -> None:
        """Returns None for an unregistered email."""

        async def _run() -> None:
            db = AsyncMock()
            db.flush = AsyncMock()

            with patch(
                "shomer.services.auth_service.get_user_by_email",
                new_callable=AsyncMock,
                return_value=None,
            ):
                svc = AuthService(db)
                token = await svc.request_password_reset(email="nobody@example.com")
                assert token is None

        asyncio.run(_run())

    def test_creates_token_in_db(self) -> None:
        """Creates a PasswordResetToken record in the database."""

        async def _run() -> None:
            db = AsyncMock()
            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()

            db.add = MagicMock()
            _flush_sets_token(db)

            with patch(
                "shomer.services.auth_service.get_user_by_email",
                new_callable=AsyncMock,
                return_value=mock_user,
            ):
                svc = AuthService(db)
                token = await svc.request_password_reset(email="user@example.com")
                assert token is not None
                db.add.assert_called_once()
                added_obj = db.add.call_args[0][0]
                assert added_obj.user_id == mock_user.id
                # used defaults to False via column default (may be None pre-flush)
                assert added_obj.used in (False, None)

        asyncio.run(_run())


class TestVerifyPasswordReset:
    """Tests for AuthService.verify_password_reset()."""

    def test_resets_password(self) -> None:
        """Valid token resets the password."""

        async def _run() -> None:
            db = AsyncMock()
            token_uuid = uuid.uuid4()

            mock_prt = MagicMock()
            mock_prt.user_id = uuid.uuid4()
            mock_prt.used = False
            mock_prt.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

            mock_current_pw = MagicMock()
            mock_current_pw.is_current = True

            # First call: find token; second call: get current password
            prt_result = MagicMock()
            prt_result.scalar_one_or_none.return_value = mock_prt
            pw_result = MagicMock()
            pw_result.scalar_one_or_none.return_value = mock_current_pw

            db.execute.side_effect = [prt_result, pw_result]
            db.add = MagicMock()
            db.flush = AsyncMock()

            with patch(
                "shomer.services.auth_service.hash_password",
                return_value="$argon2id$new",
            ):
                svc = AuthService(db)
                await svc.verify_password_reset(
                    token=token_uuid, new_password="newpassword1"
                )
                assert mock_prt.used is True
                assert mock_current_pw.is_current is False
                db.add.assert_called_once()

        asyncio.run(_run())

    def test_marks_token_as_used(self) -> None:
        """Token is marked as used after reset."""

        async def _run() -> None:
            db = AsyncMock()
            token_uuid = uuid.uuid4()

            mock_prt = MagicMock()
            mock_prt.user_id = uuid.uuid4()
            mock_prt.used = False
            mock_prt.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

            prt_result = MagicMock()
            prt_result.scalar_one_or_none.return_value = mock_prt
            pw_result = MagicMock()
            pw_result.scalar_one_or_none.return_value = MagicMock()

            db.execute.side_effect = [prt_result, pw_result]
            db.add = MagicMock()
            db.flush = AsyncMock()

            with patch("shomer.services.auth_service.hash_password"):
                svc = AuthService(db)
                await svc.verify_password_reset(
                    token=token_uuid, new_password="newpassword1"
                )
                assert mock_prt.used is True

        asyncio.run(_run())

    def test_reuse_raises(self) -> None:
        """Re-using a token raises InvalidResetTokenError."""

        async def _run() -> None:
            db = AsyncMock()

            # The query filters used==False, so a used token returns None
            prt_result = MagicMock()
            prt_result.scalar_one_or_none.return_value = None
            db.execute.return_value = prt_result

            svc = AuthService(db)
            with pytest.raises(InvalidResetTokenError):
                await svc.verify_password_reset(
                    token=uuid.uuid4(), new_password="anotherpassword"
                )

        asyncio.run(_run())

    def test_expired_token_raises(self) -> None:
        """Expired token raises InvalidResetTokenError."""

        async def _run() -> None:
            db = AsyncMock()
            token_uuid = uuid.uuid4()

            mock_prt = MagicMock()
            mock_prt.user_id = uuid.uuid4()
            mock_prt.used = False
            mock_prt.expires_at = datetime.now(timezone.utc) - timedelta(hours=2)

            prt_result = MagicMock()
            prt_result.scalar_one_or_none.return_value = mock_prt
            db.execute.return_value = prt_result

            svc = AuthService(db)
            with pytest.raises(InvalidResetTokenError):
                await svc.verify_password_reset(
                    token=token_uuid, new_password="newpassword1"
                )

        asyncio.run(_run())

    def test_invalid_token_raises(self) -> None:
        """Non-existent token raises InvalidResetTokenError."""

        async def _run() -> None:
            db = AsyncMock()

            prt_result = MagicMock()
            prt_result.scalar_one_or_none.return_value = None
            db.execute.return_value = prt_result

            svc = AuthService(db)
            with pytest.raises(InvalidResetTokenError):
                await svc.verify_password_reset(
                    token=uuid.uuid4(), new_password="newpassword1"
                )

        asyncio.run(_run())

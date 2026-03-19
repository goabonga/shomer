# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for AuthService verify and resend methods."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from shomer.services.auth_service import (
    AuthService,
    EmailNotFoundError,
    InvalidCodeError,
    RateLimitError,
)


class TestVerifyEmail:
    """Tests for AuthService.verify_email()."""

    def test_valid_code_verifies_email(self) -> None:
        """Valid code marks the email as verified."""

        async def _run() -> None:
            db = AsyncMock()

            mock_vc = MagicMock()
            mock_vc.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
            mock_vc.used = False

            mock_user_email = MagicMock()
            mock_user_email.is_verified = False
            mock_user_email.verified_at = None

            # First call: find verification code
            vc_result = MagicMock()
            vc_result.scalar_one_or_none.return_value = mock_vc
            # Second call: find user email
            email_result = MagicMock()
            email_result.scalar_one_or_none.return_value = mock_user_email

            db.execute.side_effect = [vc_result, email_result]
            db.flush = AsyncMock()

            svc = AuthService(db)
            await svc.verify_email(email="test@example.com", code="123456")

            assert mock_user_email.is_verified is True
            assert mock_user_email.verified_at is not None

        asyncio.run(_run())

    def test_code_marked_as_used(self) -> None:
        """Successful verification marks the code as used."""

        async def _run() -> None:
            db = AsyncMock()

            mock_vc = MagicMock()
            mock_vc.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
            mock_vc.used = False

            mock_user_email = MagicMock()
            mock_user_email.is_verified = False

            vc_result = MagicMock()
            vc_result.scalar_one_or_none.return_value = mock_vc
            email_result = MagicMock()
            email_result.scalar_one_or_none.return_value = mock_user_email

            db.execute.side_effect = [vc_result, email_result]
            db.flush = AsyncMock()

            svc = AuthService(db)
            await svc.verify_email(email="test@example.com", code="123456")

            assert mock_vc.used is True

        asyncio.run(_run())

    def test_wrong_code_raises(self) -> None:
        """Wrong code raises InvalidCodeError."""

        async def _run() -> None:
            db = AsyncMock()

            vc_result = MagicMock()
            vc_result.scalar_one_or_none.return_value = None
            db.execute.return_value = vc_result

            svc = AuthService(db)
            with pytest.raises(InvalidCodeError):
                await svc.verify_email(email="test@example.com", code="999999")

        asyncio.run(_run())

    def test_expired_code_raises(self) -> None:
        """Expired code raises InvalidCodeError."""

        async def _run() -> None:
            db = AsyncMock()

            mock_vc = MagicMock()
            mock_vc.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
            mock_vc.used = False

            vc_result = MagicMock()
            vc_result.scalar_one_or_none.return_value = mock_vc
            db.execute.return_value = vc_result

            svc = AuthService(db)
            with pytest.raises(InvalidCodeError):
                await svc.verify_email(email="test@example.com", code="123456")

        asyncio.run(_run())

    def test_used_code_raises(self) -> None:
        """Already-used code raises InvalidCodeError (not found query returns None)."""

        async def _run() -> None:
            db = AsyncMock()

            # The query filters used==False, so a used code returns None
            vc_result = MagicMock()
            vc_result.scalar_one_or_none.return_value = None
            db.execute.return_value = vc_result

            svc = AuthService(db)
            with pytest.raises(InvalidCodeError):
                await svc.verify_email(email="test@example.com", code="123456")

        asyncio.run(_run())


class TestResendCode:
    """Tests for AuthService.resend_code()."""

    def test_resend_generates_new_code(self) -> None:
        """Resend generates a new 6-digit code when not rate limited."""

        async def _run() -> None:
            db = AsyncMock()

            # _email_exists returns True
            email_result = MagicMock()
            email_result.scalar_one_or_none.return_value = MagicMock()

            # Rate limit check: no recent code
            rate_result = MagicMock()
            rate_result.scalar_one_or_none.return_value = None

            db.execute.side_effect = [email_result, rate_result]
            db.add = MagicMock()
            db.flush = AsyncMock()

            svc = AuthService(db)
            new_code = await svc.resend_code(email="test@example.com")
            assert len(new_code) == 6
            assert new_code.isdigit()
            db.add.assert_called_once()

        asyncio.run(_run())

    def test_resend_unknown_email_raises(self) -> None:
        """Resend with unknown email raises EmailNotFoundError."""

        async def _run() -> None:
            db = AsyncMock()

            # _email_exists returns False
            email_result = MagicMock()
            email_result.scalar_one_or_none.return_value = None
            db.execute.return_value = email_result

            svc = AuthService(db)
            with pytest.raises(EmailNotFoundError):
                await svc.resend_code(email="unknown@example.com")

        asyncio.run(_run())

    def test_resend_rate_limit(self) -> None:
        """Resend within cooldown raises RateLimitError."""

        async def _run() -> None:
            db = AsyncMock()

            # _email_exists returns True
            email_result = MagicMock()
            email_result.scalar_one_or_none.return_value = MagicMock()

            # Rate limit check: recent code found
            rate_result = MagicMock()
            rate_result.scalar_one_or_none.return_value = MagicMock()

            db.execute.side_effect = [email_result, rate_result]

            svc = AuthService(db)
            with pytest.raises(RateLimitError):
                await svc.resend_code(email="test@example.com")

        asyncio.run(_run())

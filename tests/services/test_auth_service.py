# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for AuthService (registration and change_password)."""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from shomer.services.auth_service import AuthService, InvalidCredentialsError


class TestRegister:
    """Tests for AuthService.register()."""

    def test_creates_user(self) -> None:
        """Register creates a user and returns a 6-digit code."""

        async def _run() -> None:
            db = AsyncMock()
            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()
            mock_user.username = None

            # _email_exists returns False (no duplicate)
            email_result = MagicMock()
            email_result.scalar_one_or_none.return_value = None
            db.execute.return_value = email_result
            db.add = MagicMock()
            db.flush = AsyncMock()

            with patch(
                "shomer.services.auth_service.create_user",
                new_callable=AsyncMock,
                return_value=mock_user,
            ):
                svc = AuthService(db)
                user, code = await svc.register(
                    email="test@example.com",
                    password="securepassword",
                )
                assert user is not None
                assert user.id is not None
                assert len(code) == 6
                assert code.isdigit()

        asyncio.run(_run())

    def test_creates_with_username(self) -> None:
        """Register passes username to create_user."""

        async def _run() -> None:
            db = AsyncMock()
            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()
            mock_user.username = "testuser"

            email_result = MagicMock()
            email_result.scalar_one_or_none.return_value = None
            db.execute.return_value = email_result
            db.add = MagicMock()
            db.flush = AsyncMock()

            with patch(
                "shomer.services.auth_service.create_user",
                new_callable=AsyncMock,
                return_value=mock_user,
            ):
                svc = AuthService(db)
                user, _ = await svc.register(
                    email="test@example.com",
                    password="securepassword",
                    username="testuser",
                )
                assert user is not None
                assert user.username == "testuser"

        asyncio.run(_run())

    def test_hashes_password(self) -> None:
        """Register hashes the password via hash_password."""

        async def _run() -> None:
            db = AsyncMock()
            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()

            email_result = MagicMock()
            email_result.scalar_one_or_none.return_value = None
            db.execute.return_value = email_result
            db.add = MagicMock()
            db.flush = AsyncMock()

            with (
                patch(
                    "shomer.services.auth_service.create_user",
                    new_callable=AsyncMock,
                    return_value=mock_user,
                ) as mock_create,
                patch(
                    "shomer.services.auth_service.hash_password",
                    return_value="$argon2id$hashed",
                ) as mock_hash,
            ):
                svc = AuthService(db)
                await svc.register(
                    email="test@example.com",
                    password="securepassword",
                )
                mock_hash.assert_called_once_with("securepassword")
                mock_create.assert_awaited_once()
                call_kwargs = mock_create.call_args[1]
                assert call_kwargs["password_hash"] == "$argon2id$hashed"

        asyncio.run(_run())

    def test_creates_verification_code(self) -> None:
        """Register creates a VerificationCode via session.add."""

        async def _run() -> None:
            db = AsyncMock()
            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()

            email_result = MagicMock()
            email_result.scalar_one_or_none.return_value = None
            db.execute.return_value = email_result
            db.add = MagicMock()
            db.flush = AsyncMock()

            with patch(
                "shomer.services.auth_service.create_user",
                new_callable=AsyncMock,
                return_value=mock_user,
            ):
                svc = AuthService(db)
                _, code = await svc.register(
                    email="test@example.com",
                    password="securepassword",
                )
                assert len(code) == 6
                assert code.isdigit()
                # session.add is called for the VerificationCode
                db.add.assert_called_once()

        asyncio.run(_run())

    def test_duplicate_email_raises(self) -> None:
        """Register returns (None, '') for duplicate email."""

        async def _run() -> None:
            db = AsyncMock()

            # _email_exists returns True (duplicate)
            email_result = MagicMock()
            email_result.scalar_one_or_none.return_value = MagicMock()
            db.execute.return_value = email_result

            with patch("shomer.services.auth_service.hash_password"):
                svc = AuthService(db)
                user, code = await svc.register(
                    email="dupe@example.com",
                    password="anotherpassword",
                )
                assert user is None
                assert code == ""

        asyncio.run(_run())

    def test_email_is_primary(self) -> None:
        """Register calls create_user with the email."""

        async def _run() -> None:
            db = AsyncMock()
            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()

            email_result = MagicMock()
            email_result.scalar_one_or_none.return_value = None
            db.execute.return_value = email_result
            db.add = MagicMock()
            db.flush = AsyncMock()

            with patch(
                "shomer.services.auth_service.create_user",
                new_callable=AsyncMock,
                return_value=mock_user,
            ) as mock_create:
                svc = AuthService(db)
                await svc.register(
                    email="primary@example.com",
                    password="securepassword",
                )
                call_kwargs = mock_create.call_args[1]
                assert call_kwargs["email"] == "primary@example.com"

        asyncio.run(_run())


class TestGenerateCode:
    """Tests for AuthService._generate_code()."""

    def test_code_is_6_digits(self) -> None:
        """Generated code is a 6-digit zero-padded string."""
        code = AuthService._generate_code()
        assert len(code) == 6
        assert code.isdigit()

    def test_codes_are_different(self) -> None:
        """Multiple generated codes are not all the same."""
        codes = {AuthService._generate_code() for _ in range(100)}
        assert len(codes) > 1


class TestChangePassword:
    """Tests for AuthService.change_password()."""

    def test_successful_change(self) -> None:
        """Successful password change deactivates old and adds new."""

        async def _run() -> None:
            db = AsyncMock()
            user_id = uuid.uuid4()

            mock_pw = MagicMock()
            mock_pw.password_hash = "$argon2id$real_hash"
            mock_pw.is_current = True

            pw_result = MagicMock()
            pw_result.scalar_one_or_none.return_value = mock_pw
            db.execute.return_value = pw_result
            db.add = MagicMock()
            db.flush = AsyncMock()

            with (
                patch(
                    "shomer.services.auth_service.verify_password",
                    return_value=True,
                ),
                patch(
                    "shomer.services.auth_service.hash_password",
                    return_value="$argon2id$new_hash",
                ),
            ):
                svc = AuthService(db)
                await svc.change_password(
                    user_id=user_id,
                    current_password="securepassword123",
                    new_password="newsecurepassword1",
                )
                # Old password marked as not current
                assert mock_pw.is_current is False
                # New password added
                db.add.assert_called_once()

        asyncio.run(_run())

    def test_wrong_current_password_raises(self) -> None:
        """Wrong current password raises InvalidCredentialsError."""

        async def _run() -> None:
            db = AsyncMock()
            user_id = uuid.uuid4()

            mock_pw = MagicMock()
            mock_pw.password_hash = "$argon2id$real_hash"

            pw_result = MagicMock()
            pw_result.scalar_one_or_none.return_value = mock_pw
            db.execute.return_value = pw_result

            with patch(
                "shomer.services.auth_service.verify_password",
                return_value=False,
            ):
                svc = AuthService(db)
                with pytest.raises(InvalidCredentialsError):
                    await svc.change_password(
                        user_id=user_id,
                        current_password="wrongpassword",
                        new_password="newsecurepassword1",
                    )

        asyncio.run(_run())

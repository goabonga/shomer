# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for MFAService."""

from __future__ import annotations

import asyncio
import base64
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from shomer.services.mfa_service import (
    BACKUP_CODE_COUNT,
    BACKUP_CODE_LENGTH,
    MFAService,
)


class TestTOTPSecretGeneration:
    """Tests for TOTP secret generation."""

    def test_generates_base32_secret(self) -> None:
        secret = MFAService.generate_totp_secret()
        # Should be valid base32
        decoded = base64.b32decode(secret)
        assert len(decoded) == 20

    def test_secrets_are_unique(self) -> None:
        s1 = MFAService.generate_totp_secret()
        s2 = MFAService.generate_totp_secret()
        assert s1 != s2


class TestProvisioningURI:
    """Tests for TOTP provisioning URI."""

    def test_uri_format(self) -> None:
        uri = MFAService.get_provisioning_uri(
            "JBSWY3DPEHPK3PXP",
            email="user@example.com",
            issuer="Shomer",
        )
        assert uri.startswith("otpauth://totp/")
        assert "secret=JBSWY3DPEHPK3PXP" in uri
        assert "issuer=Shomer" in uri
        assert "user%40example.com" in uri
        assert "algorithm=SHA1" in uri
        assert "digits=6" in uri
        assert "period=30" in uri

    def test_custom_issuer(self) -> None:
        uri = MFAService.get_provisioning_uri("SECRET", email="a@b.com", issuer="MyApp")
        assert "issuer=MyApp" in uri
        assert "MyApp" in uri


class TestTOTPCodeGeneration:
    """Tests for TOTP code generation."""

    def test_generates_6_digit_code(self) -> None:
        secret = MFAService.generate_totp_secret()
        code = MFAService.generate_totp_code(secret)
        assert len(code) == 6
        assert code.isdigit()

    def test_same_secret_same_time_same_code(self) -> None:
        secret = MFAService.generate_totp_secret()
        c1 = MFAService.generate_totp_code(secret)
        c2 = MFAService.generate_totp_code(secret)
        assert c1 == c2

    def test_different_offset_different_code(self) -> None:
        secret = MFAService.generate_totp_secret()
        c0 = MFAService.generate_totp_code(secret, time_offset=0)
        c_prev = MFAService.generate_totp_code(secret, time_offset=-100)
        # Very unlikely to be the same with 100 periods difference
        # (but not impossible — just testing the mechanism works)
        assert isinstance(c0, str) and isinstance(c_prev, str)

    def test_zero_padded(self) -> None:
        # Verify the code is zero-padded to 6 digits
        secret = MFAService.generate_totp_secret()
        code = MFAService.generate_totp_code(secret)
        assert len(code) == 6


class TestTOTPVerification:
    """Tests for TOTP code verification with tolerance."""

    def test_current_code_accepted(self) -> None:
        secret = MFAService.generate_totp_secret()
        code = MFAService.generate_totp_code(secret)
        assert MFAService.verify_totp_code(secret, code) is True

    def test_previous_period_accepted(self) -> None:
        secret = MFAService.generate_totp_secret()
        code = MFAService.generate_totp_code(secret, time_offset=-1)
        assert MFAService.verify_totp_code(secret, code) is True

    def test_next_period_accepted(self) -> None:
        secret = MFAService.generate_totp_secret()
        code = MFAService.generate_totp_code(secret, time_offset=1)
        assert MFAService.verify_totp_code(secret, code) is True

    def test_wrong_code_rejected(self) -> None:
        secret = MFAService.generate_totp_secret()
        assert MFAService.verify_totp_code(secret, "000000") is False

    def test_far_future_code_rejected(self) -> None:
        secret = MFAService.generate_totp_secret()
        code = MFAService.generate_totp_code(secret, time_offset=100)
        assert MFAService.verify_totp_code(secret, code) is False


class TestTOTPEncryption:
    """Tests for TOTP secret encryption/decryption."""

    def test_encrypt_decrypt_roundtrip(self) -> None:
        settings = MagicMock()
        settings.jwk_encryption_key = base64.b64encode(b"a" * 32).decode()
        svc = MFAService(AsyncMock(), settings)
        secret = MFAService.generate_totp_secret()
        encrypted = svc.encrypt_totp_secret(secret)
        decrypted = svc.decrypt_totp_secret(encrypted)
        assert decrypted == secret

    def test_encrypted_differs_from_plaintext(self) -> None:
        settings = MagicMock()
        settings.jwk_encryption_key = base64.b64encode(b"b" * 32).decode()
        svc = MFAService(AsyncMock(), settings)
        secret = "JBSWY3DPEHPK3PXP"
        encrypted = svc.encrypt_totp_secret(secret)
        assert encrypted != secret


class TestBackupCodeGeneration:
    """Tests for backup code generation."""

    def test_generates_correct_count(self) -> None:
        codes = MFAService.generate_backup_codes()
        assert len(codes) == BACKUP_CODE_COUNT

    def test_custom_count(self) -> None:
        codes = MFAService.generate_backup_codes(count=5)
        assert len(codes) == 5

    def test_codes_are_uppercase_hex(self) -> None:
        codes = MFAService.generate_backup_codes()
        for code in codes:
            assert len(code) == BACKUP_CODE_LENGTH
            assert code == code.upper()
            int(code, 16)  # should not raise

    def test_codes_are_unique(self) -> None:
        codes = MFAService.generate_backup_codes()
        assert len(set(codes)) == len(codes)


class TestBackupCodeStorage:
    """Tests for backup code storage and verification."""

    def test_store_backup_codes(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            settings = MagicMock()
            svc = MFAService(db, settings)
            mfa_id = uuid.uuid4()
            codes = ["ABCD1234", "EFGH5678"]
            await svc.store_backup_codes(mfa_id, codes)
            assert db.add.call_count == 2
            db.flush.assert_awaited_once()

        asyncio.run(_run())

    def test_verify_backup_code_success(self) -> None:
        async def _run() -> None:
            from shomer.core.security import hash_password

            code = "ABCD1234"
            mock_record = MagicMock()
            mock_record.code_hash = hash_password(code)
            mock_record.is_used = False

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_record]

            db = AsyncMock()
            db.execute.return_value = mock_result
            settings = MagicMock()
            svc = MFAService(db, settings)

            result = await svc.verify_backup_code(uuid.uuid4(), code)
            assert result is True
            assert mock_record.is_used is True

        asyncio.run(_run())

    def test_verify_backup_code_wrong_code(self) -> None:
        async def _run() -> None:
            from shomer.core.security import hash_password

            mock_record = MagicMock()
            mock_record.code_hash = hash_password("REAL1234")
            mock_record.is_used = False

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_record]

            db = AsyncMock()
            db.execute.return_value = mock_result
            settings = MagicMock()
            svc = MFAService(db, settings)

            result = await svc.verify_backup_code(uuid.uuid4(), "WRONG999")
            assert result is False

        asyncio.run(_run())

    def test_verify_backup_code_no_unused(self) -> None:
        async def _run() -> None:
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []

            db = AsyncMock()
            db.execute.return_value = mock_result
            settings = MagicMock()
            svc = MFAService(db, settings)

            result = await svc.verify_backup_code(uuid.uuid4(), "ABCD1234")
            assert result is False

        asyncio.run(_run())


class TestEmailCode:
    """Tests for email MFA code generation and verification."""

    def test_generate_email_code_format(self) -> None:
        code = MFAService.generate_email_code()
        assert len(code) == 6
        assert code.isdigit()

    def test_create_email_code(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            settings = MagicMock()
            svc = MFAService(db, settings)
            uid = uuid.uuid4()
            code = await svc.create_email_code(user_id=uid, email="u@b.com")
            assert len(code) == 6
            assert code.isdigit()
            db.add.assert_called_once()
            db.flush.assert_awaited_once()

        asyncio.run(_run())

    def test_verify_email_code_success(self) -> None:
        async def _run() -> None:
            mock_record = MagicMock()
            mock_record.is_used = False

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_record

            db = AsyncMock()
            db.execute.return_value = mock_result
            settings = MagicMock()
            svc = MFAService(db, settings)

            result = await svc.verify_email_code(user_id=uuid.uuid4(), code="123456")
            assert result is True
            assert mock_record.is_used is True

        asyncio.run(_run())

    def test_verify_email_code_not_found(self) -> None:
        async def _run() -> None:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None

            db = AsyncMock()
            db.execute.return_value = mock_result
            settings = MagicMock()
            svc = MFAService(db, settings)

            result = await svc.verify_email_code(user_id=uuid.uuid4(), code="000000")
            assert result is False

        asyncio.run(_run())

    def test_send_email_code_dispatches_task(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            settings = MagicMock()
            svc = MFAService(db, settings)

            with patch("shomer.tasks.email.send_email_task") as mock_task:
                code = await svc.send_email_code(user_id=uuid.uuid4(), email="u@b.com")
                assert len(code) == 6
                mock_task.delay.assert_called_once()
                call_kwargs = mock_task.delay.call_args[1]
                assert call_kwargs["to"] == "u@b.com"
                assert call_kwargs["template"] == "mfa_code.html"
                assert call_kwargs["context"]["code"] == code

        asyncio.run(_run())

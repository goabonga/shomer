# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Pure unit tests for MFA route handlers."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from shomer.routes.mfa import (
    EmailCodeRequest,
    MFAVerifyRequest,
    TOTPCodeRequest,
    mfa_disable,
    mfa_email_send,
    mfa_email_verify,
    mfa_enable,
    mfa_regenerate_backup_codes,
    mfa_setup,
    mfa_status,
    mfa_verify,
)


def _mock_user(user_id: str = "00000000-0000-0000-0000-000000000001") -> MagicMock:
    import uuid

    u = MagicMock()
    u.user_id = uuid.UUID(user_id)
    return u


class TestMFAStatus:
    """Unit tests for GET /mfa/status."""

    def test_no_mfa_record(self) -> None:
        async def _run() -> None:
            with patch("shomer.routes.mfa._get_user_mfa", new_callable=AsyncMock) as m:
                m.return_value = None
                resp = await mfa_status(_mock_user(), AsyncMock())
                assert resp.status_code == 200
                import json

                body = json.loads(bytes(resp.body))
                assert body["mfa_enabled"] is False
                assert body["methods"] == []

        asyncio.run(_run())

    def test_mfa_enabled(self) -> None:
        async def _run() -> None:
            mock_mfa = MagicMock()
            mock_mfa.is_enabled = True
            mock_mfa.methods = ["totp", "backup"]
            with patch("shomer.routes.mfa._get_user_mfa", new_callable=AsyncMock) as m:
                m.return_value = mock_mfa
                resp = await mfa_status(_mock_user(), AsyncMock())
                import json

                body = json.loads(bytes(resp.body))
                assert body["mfa_enabled"] is True
                assert "totp" in body["methods"]

        asyncio.run(_run())


class TestMFASetup:
    """Unit tests for POST /mfa/setup."""

    def test_setup_already_enabled_returns_409(self) -> None:
        async def _run() -> None:
            mock_mfa = MagicMock()
            mock_mfa.is_enabled = True
            with patch("shomer.routes.mfa._get_user_mfa", new_callable=AsyncMock) as m:
                m.return_value = mock_mfa
                with pytest.raises(HTTPException) as exc_info:
                    await mfa_setup(_mock_user(), AsyncMock(), MagicMock())
                assert exc_info.value.status_code == 409

        asyncio.run(_run())

    def test_setup_returns_secret_and_uri(self) -> None:
        async def _run() -> None:
            import base64

            mock_email = MagicMock()
            mock_email.email = "test@example.com"
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_email

            db = AsyncMock()
            db.execute.return_value = mock_result
            config = MagicMock()
            config.jwk_encryption_key = base64.b64encode(b"a" * 32).decode()

            with patch("shomer.routes.mfa._get_user_mfa", new_callable=AsyncMock) as m:
                m.return_value = None
                resp = await mfa_setup(_mock_user(), db, config)
                assert resp.status_code == 200
                import json

                body = json.loads(bytes(resp.body))
                assert "secret" in body
                assert "provisioning_uri" in body
                assert body["provisioning_uri"].startswith("otpauth://totp/")
                db.add.assert_called_once()

        asyncio.run(_run())


class TestMFAEnable:
    """Unit tests for POST /mfa/enable."""

    def test_enable_without_setup_returns_400(self) -> None:
        async def _run() -> None:
            with patch("shomer.routes.mfa._get_user_mfa", new_callable=AsyncMock) as m:
                m.return_value = None
                with pytest.raises(HTTPException) as exc_info:
                    await mfa_enable(
                        TOTPCodeRequest(code="123456"),
                        _mock_user(),
                        AsyncMock(),
                        MagicMock(),
                    )
                assert exc_info.value.status_code == 400

        asyncio.run(_run())

    def test_enable_already_enabled_returns_409(self) -> None:
        async def _run() -> None:
            mock_mfa = MagicMock()
            mock_mfa.is_enabled = True
            mock_mfa.totp_secret_encrypted = "enc"
            with patch("shomer.routes.mfa._get_user_mfa", new_callable=AsyncMock) as m:
                m.return_value = mock_mfa
                with pytest.raises(HTTPException) as exc_info:
                    await mfa_enable(
                        TOTPCodeRequest(code="123456"),
                        _mock_user(),
                        AsyncMock(),
                        MagicMock(),
                    )
                assert exc_info.value.status_code == 409

        asyncio.run(_run())

    def test_enable_with_wrong_code_returns_400(self) -> None:
        async def _run() -> None:
            mock_mfa = MagicMock()
            mock_mfa.is_enabled = False
            mock_mfa.totp_secret_encrypted = "enc"
            mock_mfa.id = "mfa-id"

            with (
                patch("shomer.routes.mfa._get_user_mfa", new_callable=AsyncMock) as m,
                patch("shomer.routes.mfa.MFAService") as svc_cls,
            ):
                m.return_value = mock_mfa
                mock_svc = MagicMock()
                mock_svc.decrypt_totp_secret.return_value = "JBSWY3DPEHPK3PXP"
                svc_cls.return_value = mock_svc
                svc_cls.verify_totp_code.return_value = False

                with pytest.raises(HTTPException) as exc_info:
                    await mfa_enable(
                        TOTPCodeRequest(code="000000"),
                        _mock_user(),
                        AsyncMock(),
                        MagicMock(),
                    )
                assert exc_info.value.status_code == 400

        asyncio.run(_run())

    def test_enable_success(self) -> None:
        async def _run() -> None:
            mock_mfa = MagicMock()
            mock_mfa.is_enabled = False
            mock_mfa.totp_secret_encrypted = "enc"
            mock_mfa.id = "mfa-id"
            mock_mfa.methods = []

            with (
                patch("shomer.routes.mfa._get_user_mfa", new_callable=AsyncMock) as m,
                patch("shomer.routes.mfa.MFAService") as svc_cls,
            ):
                m.return_value = mock_mfa
                mock_svc = MagicMock()
                mock_svc.decrypt_totp_secret.return_value = "JBSWY3DPEHPK3PXP"
                mock_svc.store_backup_codes = AsyncMock()
                svc_cls.return_value = mock_svc
                svc_cls.verify_totp_code.return_value = True
                svc_cls.generate_backup_codes.return_value = ["CODE1", "CODE2"]

                db = AsyncMock()
                resp = await mfa_enable(
                    TOTPCodeRequest(code="123456"),
                    _mock_user(),
                    db,
                    MagicMock(),
                )
                assert resp.status_code == 200
                import json

                body = json.loads(bytes(resp.body))
                assert body["mfa_enabled"] is True
                assert len(body["backup_codes"]) == 2

        asyncio.run(_run())


class TestMFADisable:
    """Unit tests for POST /mfa/disable."""

    def test_disable_when_not_enabled_returns_400(self) -> None:
        async def _run() -> None:
            with patch("shomer.routes.mfa._get_user_mfa", new_callable=AsyncMock) as m:
                m.return_value = None
                with pytest.raises(HTTPException) as exc_info:
                    await mfa_disable(
                        TOTPCodeRequest(code="123456"),
                        _mock_user(),
                        AsyncMock(),
                        MagicMock(),
                    )
                assert exc_info.value.status_code == 400

        asyncio.run(_run())

    def test_disable_with_wrong_code_returns_400(self) -> None:
        async def _run() -> None:
            mock_mfa = MagicMock()
            mock_mfa.is_enabled = True
            mock_mfa.totp_secret_encrypted = "enc"

            with (
                patch("shomer.routes.mfa._get_user_mfa", new_callable=AsyncMock) as m,
                patch("shomer.routes.mfa.MFAService") as svc_cls,
            ):
                m.return_value = mock_mfa
                mock_svc = MagicMock()
                mock_svc.decrypt_totp_secret.return_value = "SECRET"
                svc_cls.return_value = mock_svc
                svc_cls.verify_totp_code.return_value = False

                with pytest.raises(HTTPException) as exc_info:
                    await mfa_disable(
                        TOTPCodeRequest(code="000000"),
                        _mock_user(),
                        AsyncMock(),
                        MagicMock(),
                    )
                assert exc_info.value.status_code == 400

        asyncio.run(_run())

    def test_disable_success(self) -> None:
        async def _run() -> None:
            mock_mfa = MagicMock()
            mock_mfa.is_enabled = True
            mock_mfa.totp_secret_encrypted = "enc"

            with (
                patch("shomer.routes.mfa._get_user_mfa", new_callable=AsyncMock) as m,
                patch("shomer.routes.mfa.MFAService") as svc_cls,
            ):
                m.return_value = mock_mfa
                mock_svc = MagicMock()
                mock_svc.decrypt_totp_secret.return_value = "SECRET"
                svc_cls.return_value = mock_svc
                svc_cls.verify_totp_code.return_value = True

                db = AsyncMock()
                resp = await mfa_disable(
                    TOTPCodeRequest(code="123456"),
                    _mock_user(),
                    db,
                    MagicMock(),
                )
                assert resp.status_code == 200
                import json

                body = json.loads(bytes(resp.body))
                assert body["mfa_enabled"] is False

        asyncio.run(_run())


class TestMFABackupCodes:
    """Unit tests for POST /mfa/backup-codes."""

    def test_regenerate_when_not_enabled_returns_400(self) -> None:
        async def _run() -> None:
            with patch("shomer.routes.mfa._get_user_mfa", new_callable=AsyncMock) as m:
                m.return_value = None
                with pytest.raises(HTTPException) as exc_info:
                    await mfa_regenerate_backup_codes(
                        TOTPCodeRequest(code="123456"),
                        _mock_user(),
                        AsyncMock(),
                        MagicMock(),
                    )
                assert exc_info.value.status_code == 400

        asyncio.run(_run())

    def test_regenerate_success(self) -> None:
        async def _run() -> None:
            mock_mfa = MagicMock()
            mock_mfa.is_enabled = True
            mock_mfa.totp_secret_encrypted = "enc"
            mock_mfa.id = "mfa-id"

            mock_old_code = MagicMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_old_code]

            with (
                patch("shomer.routes.mfa._get_user_mfa", new_callable=AsyncMock) as m,
                patch("shomer.routes.mfa.MFAService") as svc_cls,
            ):
                m.return_value = mock_mfa
                mock_svc = MagicMock()
                mock_svc.decrypt_totp_secret.return_value = "SECRET"
                mock_svc.store_backup_codes = AsyncMock()
                svc_cls.return_value = mock_svc
                svc_cls.verify_totp_code.return_value = True
                svc_cls.generate_backup_codes.return_value = ["NEW1", "NEW2"]

                db = AsyncMock()
                db.execute.return_value = mock_result
                resp = await mfa_regenerate_backup_codes(
                    TOTPCodeRequest(code="123456"),
                    _mock_user(),
                    db,
                    MagicMock(),
                )
                assert resp.status_code == 200
                import json

                body = json.loads(bytes(resp.body))
                assert len(body["backup_codes"]) == 2
                db.delete.assert_awaited_once_with(mock_old_code)

        asyncio.run(_run())


class TestMFAVerify:
    """Unit tests for POST /mfa/verify."""

    def test_verify_mfa_not_enabled_returns_400(self) -> None:
        async def _run() -> None:
            with patch("shomer.routes.mfa._get_user_mfa", new_callable=AsyncMock) as m:
                m.return_value = None
                with pytest.raises(HTTPException) as exc_info:
                    await mfa_verify(
                        MFAVerifyRequest(code="123456"),
                        _mock_user(),
                        AsyncMock(),
                        MagicMock(),
                    )
                assert exc_info.value.status_code == 400

        asyncio.run(_run())

    def test_verify_totp_success(self) -> None:
        async def _run() -> None:
            mock_mfa = MagicMock()
            mock_mfa.is_enabled = True
            mock_mfa.totp_secret_encrypted = "enc"

            with (
                patch("shomer.routes.mfa._get_user_mfa", new_callable=AsyncMock) as m,
                patch("shomer.routes.mfa.MFAService") as svc_cls,
            ):
                m.return_value = mock_mfa
                mock_svc = MagicMock()
                mock_svc.decrypt_totp_secret.return_value = "SECRET"
                svc_cls.return_value = mock_svc
                svc_cls.verify_totp_code.return_value = True

                resp = await mfa_verify(
                    MFAVerifyRequest(code="123456", method="totp"),
                    _mock_user(),
                    AsyncMock(),
                    MagicMock(),
                )
                assert resp.status_code == 200
                import json

                body = json.loads(bytes(resp.body))
                assert body["verified"] is True
                assert body["method"] == "totp"

        asyncio.run(_run())

    def test_verify_totp_wrong_code_returns_400(self) -> None:
        async def _run() -> None:
            mock_mfa = MagicMock()
            mock_mfa.is_enabled = True
            mock_mfa.totp_secret_encrypted = "enc"

            with (
                patch("shomer.routes.mfa._get_user_mfa", new_callable=AsyncMock) as m,
                patch("shomer.routes.mfa.MFAService") as svc_cls,
            ):
                m.return_value = mock_mfa
                mock_svc = MagicMock()
                mock_svc.decrypt_totp_secret.return_value = "SECRET"
                svc_cls.return_value = mock_svc
                svc_cls.verify_totp_code.return_value = False

                with pytest.raises(HTTPException) as exc_info:
                    await mfa_verify(
                        MFAVerifyRequest(code="000000"),
                        _mock_user(),
                        AsyncMock(),
                        MagicMock(),
                    )
                assert exc_info.value.status_code == 400

        asyncio.run(_run())

    def test_verify_backup_success(self) -> None:
        async def _run() -> None:
            mock_mfa = MagicMock()
            mock_mfa.is_enabled = True
            mock_mfa.id = "mfa-id"

            with (
                patch("shomer.routes.mfa._get_user_mfa", new_callable=AsyncMock) as m,
                patch("shomer.routes.mfa.MFAService") as svc_cls,
            ):
                m.return_value = mock_mfa
                mock_svc = MagicMock()
                mock_svc.verify_backup_code = AsyncMock(return_value=True)
                svc_cls.return_value = mock_svc

                resp = await mfa_verify(
                    MFAVerifyRequest(code="ABCD1234", method="backup"),
                    _mock_user(),
                    AsyncMock(),
                    MagicMock(),
                )
                assert resp.status_code == 200
                import json

                body = json.loads(bytes(resp.body))
                assert body["method"] == "backup"

        asyncio.run(_run())

    def test_verify_backup_invalid_returns_400(self) -> None:
        async def _run() -> None:
            mock_mfa = MagicMock()
            mock_mfa.is_enabled = True
            mock_mfa.id = "mfa-id"

            with (
                patch("shomer.routes.mfa._get_user_mfa", new_callable=AsyncMock) as m,
                patch("shomer.routes.mfa.MFAService") as svc_cls,
            ):
                m.return_value = mock_mfa
                mock_svc = MagicMock()
                mock_svc.verify_backup_code = AsyncMock(return_value=False)
                svc_cls.return_value = mock_svc

                with pytest.raises(HTTPException) as exc_info:
                    await mfa_verify(
                        MFAVerifyRequest(code="WRONG", method="backup"),
                        _mock_user(),
                        AsyncMock(),
                        MagicMock(),
                    )
                assert exc_info.value.status_code == 400

        asyncio.run(_run())


class TestMFAEmailSend:
    """Unit tests for POST /mfa/email/send."""

    def test_email_send_mfa_not_enabled_returns_400(self) -> None:
        async def _run() -> None:
            with patch("shomer.routes.mfa._get_user_mfa", new_callable=AsyncMock) as m:
                m.return_value = None
                with pytest.raises(HTTPException) as exc_info:
                    await mfa_email_send(_mock_user(), AsyncMock(), MagicMock())
                assert exc_info.value.status_code == 400

        asyncio.run(_run())

    def test_email_send_rate_limited_returns_429(self) -> None:
        async def _run() -> None:
            mock_mfa = MagicMock()
            mock_mfa.is_enabled = True

            mock_count_result = MagicMock()
            mock_count_result.scalar.return_value = 5

            db = AsyncMock()
            db.execute.return_value = mock_count_result

            with patch("shomer.routes.mfa._get_user_mfa", new_callable=AsyncMock) as m:
                m.return_value = mock_mfa
                with pytest.raises(HTTPException) as exc_info:
                    await mfa_email_send(_mock_user(), db, MagicMock())
                assert exc_info.value.status_code == 429

        asyncio.run(_run())

    def test_email_send_success(self) -> None:
        async def _run() -> None:
            mock_mfa = MagicMock()
            mock_mfa.is_enabled = True

            mock_count_result = MagicMock()
            mock_count_result.scalar.return_value = 0

            mock_email = MagicMock()
            mock_email.email = "user@example.com"
            mock_email_result = MagicMock()
            mock_email_result.scalar_one_or_none.return_value = mock_email

            db = AsyncMock()
            db.execute.side_effect = [mock_count_result, mock_email_result]

            with (
                patch("shomer.routes.mfa._get_user_mfa", new_callable=AsyncMock) as m,
                patch("shomer.routes.mfa.MFAService") as svc_cls,
            ):
                m.return_value = mock_mfa
                mock_svc = MagicMock()
                mock_svc.send_email_code = AsyncMock(return_value="123456")
                svc_cls.return_value = mock_svc

                resp = await mfa_email_send(_mock_user(), db, MagicMock())
                assert resp.status_code == 200
                import json

                body = json.loads(bytes(resp.body))
                assert body["sent"] is True

        asyncio.run(_run())


class TestMFAEmailVerify:
    """Unit tests for POST /mfa/email/verify."""

    def test_email_verify_mfa_not_enabled_returns_400(self) -> None:
        async def _run() -> None:
            with patch("shomer.routes.mfa._get_user_mfa", new_callable=AsyncMock) as m:
                m.return_value = None
                with pytest.raises(HTTPException) as exc_info:
                    await mfa_email_verify(
                        EmailCodeRequest(code="123456"),
                        _mock_user(),
                        AsyncMock(),
                        MagicMock(),
                    )
                assert exc_info.value.status_code == 400

        asyncio.run(_run())

    def test_email_verify_success(self) -> None:
        async def _run() -> None:
            mock_mfa = MagicMock()
            mock_mfa.is_enabled = True

            with (
                patch("shomer.routes.mfa._get_user_mfa", new_callable=AsyncMock) as m,
                patch("shomer.routes.mfa.MFAService") as svc_cls,
            ):
                m.return_value = mock_mfa
                mock_svc = MagicMock()
                mock_svc.verify_email_code = AsyncMock(return_value=True)
                svc_cls.return_value = mock_svc

                resp = await mfa_email_verify(
                    EmailCodeRequest(code="123456"),
                    _mock_user(),
                    AsyncMock(),
                    MagicMock(),
                )
                assert resp.status_code == 200
                import json

                body = json.loads(bytes(resp.body))
                assert body["verified"] is True
                assert body["method"] == "email"

        asyncio.run(_run())

    def test_email_verify_invalid_returns_400(self) -> None:
        async def _run() -> None:
            mock_mfa = MagicMock()
            mock_mfa.is_enabled = True

            with (
                patch("shomer.routes.mfa._get_user_mfa", new_callable=AsyncMock) as m,
                patch("shomer.routes.mfa.MFAService") as svc_cls,
            ):
                m.return_value = mock_mfa
                mock_svc = MagicMock()
                mock_svc.verify_email_code = AsyncMock(return_value=False)
                svc_cls.return_value = mock_svc

                with pytest.raises(HTTPException) as exc_info:
                    await mfa_email_verify(
                        EmailCodeRequest(code="000000"),
                        _mock_user(),
                        AsyncMock(),
                        MagicMock(),
                    )
                assert exc_info.value.status_code == 400

        asyncio.run(_run())

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for Device Authorization service."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from shomer.models.device_code import DeviceCodeStatus
from shomer.services.device_auth_service import (
    DeviceAuthError,
    DeviceAuthService,
)


class TestCreateDeviceCode:
    """Tests for DeviceAuthService.create_device_code()."""

    def test_creates_device_code(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            svc = DeviceAuthService(db)
            resp = await svc.create_device_code(
                client_id="tv-app",
                scopes="openid profile",
                verification_uri="https://auth.example.com/device",
            )
            assert resp.device_code is not None
            assert len(resp.device_code) > 10
            assert "-" in resp.user_code
            assert len(resp.user_code) == 9  # XXXX-XXXX
            assert resp.verification_uri == "https://auth.example.com/device"
            assert resp.verification_uri_complete is not None
            assert resp.user_code in resp.verification_uri_complete
            assert resp.interval == 5
            assert resp.expires_in == 900
            db.add.assert_called_once()

        asyncio.run(_run())

    def test_user_codes_are_unique(self) -> None:
        codes = {DeviceAuthService._generate_user_code() for _ in range(50)}
        assert len(codes) == 50

    def test_user_code_format(self) -> None:
        code = DeviceAuthService._generate_user_code()
        parts = code.split("-")
        assert len(parts) == 2
        assert len(parts[0]) == 4
        assert len(parts[1]) == 4
        assert parts[0].isalpha()
        assert parts[1].isalpha()


class TestApprove:
    """Tests for DeviceAuthService.approve()."""

    def test_approve_sets_status_and_user(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            db.flush = AsyncMock()
            uid = uuid.uuid4()

            mock_dc = MagicMock()
            mock_dc.status = DeviceCodeStatus.PENDING
            mock_dc.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_dc
            db.execute.return_value = result

            svc = DeviceAuthService(db)
            dc = await svc.approve(user_code="ABCD-EFGH", user_id=uid)
            assert dc.status == DeviceCodeStatus.APPROVED
            assert dc.user_id == uid

        asyncio.run(_run())

    def test_approve_unknown_code_raises(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db.execute.return_value = result

            svc = DeviceAuthService(db)
            with pytest.raises(DeviceAuthError, match="Unknown user code"):
                await svc.approve(user_code="XXXX-XXXX", user_id=uuid.uuid4())

        asyncio.run(_run())

    def test_approve_expired_code_raises(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            mock_dc = MagicMock()
            mock_dc.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_dc
            db.execute.return_value = result

            svc = DeviceAuthService(db)
            with pytest.raises(DeviceAuthError, match="expired"):
                await svc.approve(user_code="XXXX-XXXX", user_id=uuid.uuid4())

        asyncio.run(_run())

    def test_approve_already_approved_raises(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            mock_dc = MagicMock()
            mock_dc.status = DeviceCodeStatus.APPROVED
            mock_dc.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_dc
            db.execute.return_value = result

            svc = DeviceAuthService(db)
            with pytest.raises(DeviceAuthError, match="not pending"):
                await svc.approve(user_code="XXXX-XXXX", user_id=uuid.uuid4())

        asyncio.run(_run())


class TestDeny:
    """Tests for DeviceAuthService.deny()."""

    def test_deny_sets_status(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            db.flush = AsyncMock()

            mock_dc = MagicMock()
            mock_dc.status = DeviceCodeStatus.PENDING
            mock_dc.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_dc
            db.execute.return_value = result

            svc = DeviceAuthService(db)
            dc = await svc.deny(user_code="ABCD-EFGH")
            assert dc.status == DeviceCodeStatus.DENIED

        asyncio.run(_run())


class TestCheckStatus:
    """Tests for DeviceAuthService.check_status()."""

    def test_pending_status(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            mock_dc = MagicMock()
            mock_dc.status = DeviceCodeStatus.PENDING
            mock_dc.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_dc
            db.execute.return_value = result

            svc = DeviceAuthService(db)
            dc = await svc.check_status(device_code="dev-code")
            assert dc.status == DeviceCodeStatus.PENDING

        asyncio.run(_run())

    def test_approved_status(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            mock_dc = MagicMock()
            mock_dc.status = DeviceCodeStatus.APPROVED
            mock_dc.user_id = uuid.uuid4()
            mock_dc.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_dc
            db.execute.return_value = result

            svc = DeviceAuthService(db)
            dc = await svc.check_status(device_code="dev-code")
            assert dc.status == DeviceCodeStatus.APPROVED

        asyncio.run(_run())

    def test_unknown_device_code_raises(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db.execute.return_value = result

            svc = DeviceAuthService(db)
            with pytest.raises(DeviceAuthError, match="Unknown device code"):
                await svc.check_status(device_code="unknown")

        asyncio.run(_run())

    def test_expired_code_sets_status_and_raises(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            db.flush = AsyncMock()
            mock_dc = MagicMock()
            mock_dc.status = DeviceCodeStatus.PENDING
            mock_dc.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_dc
            db.execute.return_value = result

            svc = DeviceAuthService(db)
            with pytest.raises(DeviceAuthError, match="expired"):
                await svc.check_status(device_code="dev-code")
            assert mock_dc.status == DeviceCodeStatus.EXPIRED

        asyncio.run(_run())


class TestExpireOldCodes:
    """Tests for DeviceAuthService.expire_old_codes()."""

    def test_expire_old_codes(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            db.flush = AsyncMock()
            mock_result = MagicMock()
            mock_result.rowcount = 3
            db.execute.return_value = mock_result

            svc = DeviceAuthService(db)
            count = await svc.expire_old_codes()
            assert count == 3

        asyncio.run(_run())

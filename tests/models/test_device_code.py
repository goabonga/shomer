# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for DeviceCode model."""

from datetime import datetime, timezone

from shomer.models.device_code import DeviceCode, DeviceCodeStatus


class TestDeviceCodeModel:
    """Tests for DeviceCode SQLAlchemy model definition."""

    def test_tablename(self) -> None:
        assert DeviceCode.__tablename__ == "device_codes"

    def test_required_fields(self) -> None:
        now = datetime.now(timezone.utc)
        dc = DeviceCode(
            device_code="dev-code-123",
            user_code="ABCD-EFGH",
            client_id="my-client",
            scopes="openid profile",
            verification_uri="https://auth.example.com/device",
            expires_at=now,
        )
        assert dc.device_code == "dev-code-123"
        assert dc.user_code == "ABCD-EFGH"
        assert dc.client_id == "my-client"
        assert dc.scopes == "openid profile"
        assert dc.verification_uri == "https://auth.example.com/device"
        assert dc.expires_at == now

    def test_default_status(self) -> None:
        col = DeviceCode.__table__.c.status
        assert col.default.arg == DeviceCodeStatus.PENDING

    def test_default_interval(self) -> None:
        col = DeviceCode.__table__.c.interval
        assert col.default.arg == 5

    def test_device_code_unique(self) -> None:
        col = DeviceCode.__table__.c.device_code
        assert col.unique is True

    def test_user_code_unique(self) -> None:
        col = DeviceCode.__table__.c.user_code
        assert col.unique is True

    def test_device_code_indexed(self) -> None:
        col = DeviceCode.__table__.c.device_code
        assert col.index is True

    def test_user_code_indexed(self) -> None:
        col = DeviceCode.__table__.c.user_code
        assert col.index is True

    def test_user_id_nullable(self) -> None:
        col = DeviceCode.__table__.c.user_id
        assert col.nullable is True

    def test_user_id_foreign_key(self) -> None:
        col = DeviceCode.__table__.c.user_id
        fk = list(col.foreign_keys)[0]
        assert fk.column.table.name == "users"

    def test_verification_uri_complete_nullable(self) -> None:
        col = DeviceCode.__table__.c.verification_uri_complete
        assert col.nullable is True

    def test_repr(self) -> None:
        dc = DeviceCode(
            device_code="x",
            user_code="ABCD-EFGH",
            client_id="c",
            verification_uri="https://x",
            expires_at=datetime.now(timezone.utc),
            status=DeviceCodeStatus.PENDING,
        )
        r = repr(dc)
        assert "ABCD-EFGH" in r
        assert "pending" in r


class TestDeviceCodeStatus:
    """Tests for DeviceCodeStatus enum."""

    def test_pending(self) -> None:
        assert DeviceCodeStatus.PENDING.value == "pending"

    def test_approved(self) -> None:
        assert DeviceCodeStatus.APPROVED.value == "approved"

    def test_denied(self) -> None:
        assert DeviceCodeStatus.DENIED.value == "denied"

    def test_expired(self) -> None:
        assert DeviceCodeStatus.EXPIRED.value == "expired"

    def test_all_values(self) -> None:
        values = {s.value for s in DeviceCodeStatus}
        assert values == {"pending", "approved", "denied", "expired"}

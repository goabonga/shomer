# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for VerificationCode model."""

from datetime import datetime, timezone

from shomer.models.verification_code import VerificationCode


class TestVerificationCodeModel:
    """Tests for VerificationCode SQLAlchemy model definition."""

    def test_tablename(self) -> None:
        assert VerificationCode.__tablename__ == "verification_codes"

    def test_required_fields(self) -> None:
        now = datetime.now(timezone.utc)
        vc = VerificationCode(
            email="user@example.com",
            code="123456",
            expires_at=now,
        )
        assert vc.email == "user@example.com"
        assert vc.code == "123456"
        assert vc.expires_at == now

    def test_used_column_defaults(self) -> None:
        col = VerificationCode.__table__.c.used
        assert col.nullable is False
        assert col.default.arg is False

    def test_email_column_indexed(self) -> None:
        col = VerificationCode.__table__.c.email
        assert col.index is True

    def test_email_column_not_nullable(self) -> None:
        col = VerificationCode.__table__.c.email
        assert col.nullable is False

    def test_code_column_not_nullable(self) -> None:
        col = VerificationCode.__table__.c.code
        assert col.nullable is False

    def test_expires_at_not_nullable(self) -> None:
        col = VerificationCode.__table__.c.expires_at
        assert col.nullable is False

    def test_repr(self) -> None:
        now = datetime.now(timezone.utc)
        vc = VerificationCode(
            email="a@b.com",
            code="000000",
            expires_at=now,
        )
        assert "email=a@b.com" in repr(vc)

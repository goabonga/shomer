# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for MFAEmailCode model."""

import uuid
from datetime import datetime, timezone

from shomer.models.mfa_email_code import MFAEmailCode


class TestMFAEmailCodeModel:
    """Tests for MFAEmailCode SQLAlchemy model definition."""

    def test_tablename(self) -> None:
        assert MFAEmailCode.__tablename__ == "mfa_email_codes"

    def test_required_fields(self) -> None:
        now = datetime.now(timezone.utc)
        uid = uuid.uuid4()
        ec = MFAEmailCode(
            user_id=uid,
            email="user@example.com",
            code="123456",
            expires_at=now,
            is_used=False,
        )
        assert ec.user_id == uid
        assert ec.email == "user@example.com"
        assert ec.code == "123456"
        assert ec.expires_at == now
        assert ec.is_used is False

    def test_mark_as_used(self) -> None:
        ec = MFAEmailCode(
            user_id=uuid.uuid4(),
            email="u@b.com",
            code="654321",
            expires_at=datetime.now(timezone.utc),
            is_used=True,
        )
        assert ec.is_used is True

    def test_code_max_length_6(self) -> None:
        col = MFAEmailCode.__table__.c.code
        assert getattr(col.type, "length", None) == 6

    def test_user_id_indexed(self) -> None:
        col = MFAEmailCode.__table__.c.user_id
        assert col.index is True

    def test_repr(self) -> None:
        uid = uuid.uuid4()
        ec = MFAEmailCode(
            user_id=uid,
            email="test@example.com",
            code="111111",
            expires_at=datetime.now(timezone.utc),
        )
        r = repr(ec)
        assert str(uid) in r
        assert "test@example.com" in r

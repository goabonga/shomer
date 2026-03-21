# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for UserMFA model."""

import uuid

from shomer.models.user_mfa import UserMFA


class TestUserMFAModel:
    """Tests for UserMFA SQLAlchemy model definition."""

    def test_tablename(self) -> None:
        assert UserMFA.__tablename__ == "user_mfa"

    def test_required_fields(self) -> None:
        uid = uuid.uuid4()
        mfa = UserMFA(user_id=uid, is_enabled=False, methods=[])
        assert mfa.user_id == uid
        assert mfa.is_enabled is False
        assert mfa.methods == []
        assert mfa.totp_secret_encrypted is None

    def test_enabled_with_methods(self) -> None:
        mfa = UserMFA(
            user_id=uuid.uuid4(),
            is_enabled=True,
            methods=["totp", "backup"],
        )
        assert mfa.is_enabled is True
        assert "totp" in mfa.methods
        assert "backup" in mfa.methods

    def test_totp_secret_stored(self) -> None:
        mfa = UserMFA(
            user_id=uuid.uuid4(),
            totp_secret_encrypted="encrypted-base32-secret",
        )
        assert mfa.totp_secret_encrypted == "encrypted-base32-secret"

    def test_user_id_unique(self) -> None:
        col = UserMFA.__table__.c.user_id
        assert col.unique is True

    def test_user_id_indexed(self) -> None:
        col = UserMFA.__table__.c.user_id
        assert col.index is True

    def test_repr(self) -> None:
        uid = uuid.uuid4()
        mfa = UserMFA(user_id=uid, is_enabled=True)
        r = repr(mfa)
        assert str(uid) in r
        assert "True" in r

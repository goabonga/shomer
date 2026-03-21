# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for MFABackupCode model."""

import uuid

from shomer.models.mfa_backup_code import MFABackupCode


class TestMFABackupCodeModel:
    """Tests for MFABackupCode SQLAlchemy model definition."""

    def test_tablename(self) -> None:
        assert MFABackupCode.__tablename__ == "mfa_backup_codes"

    def test_required_fields(self) -> None:
        mfa_id = uuid.uuid4()
        code = MFABackupCode(
            user_mfa_id=mfa_id,
            code_hash="$argon2id$v=19$m=65536,t=3,p=4$hash",
            is_used=False,
        )
        assert code.user_mfa_id == mfa_id
        assert code.code_hash.startswith("$argon2id")
        assert code.is_used is False

    def test_mark_as_used(self) -> None:
        code = MFABackupCode(
            user_mfa_id=uuid.uuid4(),
            code_hash="hash",
            is_used=True,
        )
        assert code.is_used is True

    def test_user_mfa_id_indexed(self) -> None:
        col = MFABackupCode.__table__.c.user_mfa_id
        assert col.index is True

    def test_repr(self) -> None:
        code = MFABackupCode(
            user_mfa_id=uuid.uuid4(),
            code_hash="hash",
            is_used=False,
        )
        r = repr(code)
        assert "MFABackupCode" in r
        assert "False" in r

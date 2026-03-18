# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for PasswordResetToken model."""

import uuid
from datetime import datetime, timezone

from shomer.models.password_reset_token import PasswordResetToken
from shomer.models.user import User  # noqa: F401 — register mapper
from shomer.models.user_email import UserEmail  # noqa: F401 — register mapper
from shomer.models.user_password import UserPassword  # noqa: F401 — register mapper
from shomer.models.user_profile import UserProfile  # noqa: F401 — register mapper


class TestPasswordResetTokenModel:
    """Tests for PasswordResetToken SQLAlchemy model definition."""

    def test_tablename(self) -> None:
        assert PasswordResetToken.__tablename__ == "password_reset_tokens"

    def test_required_fields(self) -> None:
        now = datetime.now(timezone.utc)
        uid = uuid.uuid4()
        tok = uuid.uuid4()
        prt = PasswordResetToken(
            token=tok,
            user_id=uid,
            expires_at=now,
        )
        assert prt.token == tok
        assert prt.user_id == uid
        assert prt.expires_at == now

    def test_used_column_defaults(self) -> None:
        col = PasswordResetToken.__table__.c.used
        assert col.nullable is False
        assert col.default.arg is False

    def test_token_column_unique(self) -> None:
        col = PasswordResetToken.__table__.c.token
        assert col.unique is True

    def test_token_column_indexed(self) -> None:
        col = PasswordResetToken.__table__.c.token
        assert col.index is True

    def test_token_column_not_nullable(self) -> None:
        col = PasswordResetToken.__table__.c.token
        assert col.nullable is False

    def test_user_id_column_not_nullable(self) -> None:
        col = PasswordResetToken.__table__.c.user_id
        assert col.nullable is False

    def test_user_id_column_indexed(self) -> None:
        col = PasswordResetToken.__table__.c.user_id
        assert col.index is True

    def test_expires_at_not_nullable(self) -> None:
        col = PasswordResetToken.__table__.c.expires_at
        assert col.nullable is False

    def test_user_id_foreign_key(self) -> None:
        col = PasswordResetToken.__table__.c.user_id
        fk = list(col.foreign_keys)[0]
        assert fk.column.table.name == "users"
        assert fk.column.name == "id"

    def test_repr(self) -> None:
        now = datetime.now(timezone.utc)
        uid = uuid.uuid4()
        prt = PasswordResetToken(
            token=uuid.uuid4(),
            user_id=uid,
            expires_at=now,
        )
        assert f"user_id={uid}" in repr(prt)


class TestPasswordResetTokenRelationship:
    """Tests for PasswordResetToken <-> User relationship."""

    def test_user_relationship_exists(self) -> None:
        rel = PasswordResetToken.__mapper__.relationships["user"]
        assert rel.back_populates == "password_reset_tokens"

    def test_user_model_has_password_reset_tokens_relationship(self) -> None:
        rel = User.__mapper__.relationships["password_reset_tokens"]
        assert rel.back_populates == "user"

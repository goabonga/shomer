# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for RefreshToken model."""

import uuid
from datetime import datetime, timezone

from shomer.models.refresh_token import RefreshToken
from shomer.models.user import User  # noqa: F401
from shomer.models.user_email import UserEmail  # noqa: F401
from shomer.models.user_password import UserPassword  # noqa: F401
from shomer.models.user_profile import UserProfile  # noqa: F401


class TestRefreshTokenModel:
    """Tests for RefreshToken SQLAlchemy model definition."""

    def test_tablename(self) -> None:
        assert RefreshToken.__tablename__ == "refresh_tokens"

    def test_required_fields(self) -> None:
        now = datetime.now(timezone.utc)
        fid = uuid.uuid4()
        rt = RefreshToken(
            token_hash="hashed_value",
            family_id=fid,
            user_id=uuid.uuid4(),
            client_id="my-client",
            scopes="openid",
            expires_at=now,
        )
        assert rt.token_hash == "hashed_value"
        assert rt.family_id == fid
        assert rt.client_id == "my-client"
        assert rt.scopes == "openid"

    def test_revoked_default(self) -> None:
        col = RefreshToken.__table__.c.revoked
        assert col.nullable is False
        assert col.default.arg is False

    def test_replaced_by_nullable(self) -> None:
        col = RefreshToken.__table__.c.replaced_by
        assert col.nullable is True

    def test_family_id_indexed(self) -> None:
        col = RefreshToken.__table__.c.family_id
        assert col.index is True

    def test_user_id_indexed(self) -> None:
        col = RefreshToken.__table__.c.user_id
        assert col.index is True

    def test_user_id_not_nullable(self) -> None:
        col = RefreshToken.__table__.c.user_id
        assert col.nullable is False

    def test_user_id_foreign_key(self) -> None:
        col = RefreshToken.__table__.c.user_id
        fk = list(col.foreign_keys)[0]
        assert fk.column.table.name == "users"

    def test_token_hash_not_nullable(self) -> None:
        col = RefreshToken.__table__.c.token_hash
        assert col.nullable is False

    def test_family_id_not_nullable(self) -> None:
        col = RefreshToken.__table__.c.family_id
        assert col.nullable is False

    def test_repr(self) -> None:
        fid = uuid.uuid4()
        rt = RefreshToken(
            token_hash="h",
            family_id=fid,
            user_id=uuid.uuid4(),
            client_id="c",
            expires_at=datetime.now(timezone.utc),
        )
        assert f"family={fid}" in repr(rt)


class TestRefreshTokenRelationship:
    """Tests for RefreshToken <-> User relationship."""

    def test_user_relationship_exists(self) -> None:
        rel = RefreshToken.__mapper__.relationships["user"]
        assert rel.back_populates == "refresh_tokens"

    def test_user_model_has_refresh_tokens(self) -> None:
        rel = User.__mapper__.relationships["refresh_tokens"]
        assert rel.back_populates == "user"

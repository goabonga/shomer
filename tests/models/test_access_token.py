# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for AccessToken model."""

import uuid
from datetime import datetime, timezone

from shomer.models.access_token import AccessToken
from shomer.models.user import User  # noqa: F401
from shomer.models.user_email import UserEmail  # noqa: F401
from shomer.models.user_password import UserPassword  # noqa: F401
from shomer.models.user_profile import UserProfile  # noqa: F401


class TestAccessTokenModel:
    """Tests for AccessToken SQLAlchemy model definition."""

    def test_tablename(self) -> None:
        assert AccessToken.__tablename__ == "access_tokens"

    def test_required_fields(self) -> None:
        now = datetime.now(timezone.utc)
        at = AccessToken(
            jti="abc123",
            user_id=uuid.uuid4(),
            client_id="my-client",
            scopes="openid profile",
            expires_at=now,
        )
        assert at.jti == "abc123"
        assert at.client_id == "my-client"
        assert at.scopes == "openid profile"
        assert at.expires_at == now

    def test_revoked_default(self) -> None:
        col = AccessToken.__table__.c.revoked
        assert col.nullable is False
        assert col.default.arg is False

    def test_jti_unique(self) -> None:
        col = AccessToken.__table__.c.jti
        assert col.unique is True

    def test_jti_indexed(self) -> None:
        col = AccessToken.__table__.c.jti
        assert col.index is True

    def test_user_id_indexed(self) -> None:
        col = AccessToken.__table__.c.user_id
        assert col.index is True

    def test_user_id_not_nullable(self) -> None:
        col = AccessToken.__table__.c.user_id
        assert col.nullable is False

    def test_user_id_foreign_key(self) -> None:
        col = AccessToken.__table__.c.user_id
        fk = list(col.foreign_keys)[0]
        assert fk.column.table.name == "users"

    def test_repr(self) -> None:
        at = AccessToken(
            jti="x",
            user_id=uuid.uuid4(),
            client_id="c",
            expires_at=datetime.now(timezone.utc),
        )
        assert "jti=x" in repr(at)


class TestAccessTokenRelationship:
    """Tests for AccessToken <-> User relationship."""

    def test_user_relationship_exists(self) -> None:
        rel = AccessToken.__mapper__.relationships["user"]
        assert rel.back_populates == "access_tokens"

    def test_user_model_has_access_tokens(self) -> None:
        rel = User.__mapper__.relationships["access_tokens"]
        assert rel.back_populates == "user"

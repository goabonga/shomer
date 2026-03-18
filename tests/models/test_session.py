# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for Session model."""

import uuid
from datetime import datetime, timezone

from shomer.models.session import Session
from shomer.models.user import User  # noqa: F401 — register mapper
from shomer.models.user_email import UserEmail  # noqa: F401 — register mapper
from shomer.models.user_password import UserPassword  # noqa: F401 — register mapper


class TestSessionModel:
    """Tests for Session SQLAlchemy model definition."""

    def test_tablename(self) -> None:
        assert Session.__tablename__ == "sessions"

    def test_required_fields(self) -> None:
        now = datetime.now(timezone.utc)
        session = Session(
            user_id=uuid.uuid4(),
            token_hash="hashed_token",
            csrf_token="csrf_abc123",
            last_activity=now,
            expires_at=now,
        )
        assert session.token_hash == "hashed_token"
        assert session.csrf_token == "csrf_abc123"
        assert session.last_activity == now
        assert session.expires_at == now

    def test_nullable_fields_default_none(self) -> None:
        now = datetime.now(timezone.utc)
        session = Session(
            user_id=uuid.uuid4(),
            token_hash="h",
            csrf_token="c",
            last_activity=now,
            expires_at=now,
        )
        assert session.tenant_id is None
        assert session.user_agent is None
        assert session.ip_address is None

    def test_optional_fields(self) -> None:
        now = datetime.now(timezone.utc)
        tid = uuid.uuid4()
        session = Session(
            user_id=uuid.uuid4(),
            tenant_id=tid,
            token_hash="h",
            csrf_token="c",
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.1",
            last_activity=now,
            expires_at=now,
        )
        assert session.tenant_id == tid
        assert session.user_agent == "Mozilla/5.0"
        assert session.ip_address == "192.168.1.1"

    def test_repr(self) -> None:
        now = datetime.now(timezone.utc)
        uid = uuid.uuid4()
        session = Session(
            user_id=uid,
            token_hash="h",
            csrf_token="c",
            last_activity=now,
            expires_at=now,
        )
        assert f"user_id={uid}" in repr(session)

    def test_user_id_column_not_nullable(self) -> None:
        col = Session.__table__.c.user_id
        assert col.nullable is False

    def test_user_id_column_indexed(self) -> None:
        col = Session.__table__.c.user_id
        assert col.index is True

    def test_tenant_id_column_nullable(self) -> None:
        col = Session.__table__.c.tenant_id
        assert col.nullable is True

    def test_tenant_id_column_indexed(self) -> None:
        col = Session.__table__.c.tenant_id
        assert col.index is True

    def test_token_hash_not_nullable(self) -> None:
        col = Session.__table__.c.token_hash
        assert col.nullable is False

    def test_csrf_token_not_nullable(self) -> None:
        col = Session.__table__.c.csrf_token
        assert col.nullable is False

    def test_last_activity_not_nullable(self) -> None:
        col = Session.__table__.c.last_activity
        assert col.nullable is False

    def test_expires_at_not_nullable(self) -> None:
        col = Session.__table__.c.expires_at
        assert col.nullable is False

    def test_user_id_foreign_key(self) -> None:
        col = Session.__table__.c.user_id
        fk = list(col.foreign_keys)[0]
        assert fk.column.table.name == "users"
        assert fk.column.name == "id"


class TestSessionRelationship:
    """Tests for Session <-> User relationship configuration."""

    def test_user_relationship_exists(self) -> None:
        rel = Session.__mapper__.relationships["user"]
        assert rel.back_populates == "sessions"

    def test_user_model_has_sessions_relationship(self) -> None:
        rel = User.__mapper__.relationships["sessions"]
        assert rel.back_populates == "user"

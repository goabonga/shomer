# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for AuthorizationCode model."""

import uuid
from datetime import datetime, timedelta, timezone

from shomer.models.authorization_code import AuthorizationCode
from shomer.models.user import User  # noqa: F401
from shomer.models.user_email import UserEmail  # noqa: F401
from shomer.models.user_password import UserPassword  # noqa: F401
from shomer.models.user_profile import UserProfile  # noqa: F401


class TestAuthorizationCodeModel:
    """Tests for AuthorizationCode SQLAlchemy model definition."""

    def test_tablename(self) -> None:
        assert AuthorizationCode.__tablename__ == "authorization_codes"

    def test_required_fields(self) -> None:
        now = datetime.now(timezone.utc)
        ac = AuthorizationCode(
            code="abc123def456",
            user_id=uuid.uuid4(),
            client_id="my-client",
            redirect_uri="https://app.example.com/callback",
            scopes="openid profile",
            expires_at=now + timedelta(minutes=10),
        )
        assert ac.code == "abc123def456"
        assert ac.client_id == "my-client"
        assert ac.redirect_uri == "https://app.example.com/callback"
        assert ac.scopes == "openid profile"

    def test_code_unique(self) -> None:
        col = AuthorizationCode.__table__.c.code
        assert col.unique is True

    def test_code_indexed(self) -> None:
        col = AuthorizationCode.__table__.c.code
        assert col.index is True

    def test_code_not_nullable(self) -> None:
        col = AuthorizationCode.__table__.c.code
        assert col.nullable is False

    def test_user_id_indexed(self) -> None:
        col = AuthorizationCode.__table__.c.user_id
        assert col.index is True

    def test_user_id_not_nullable(self) -> None:
        col = AuthorizationCode.__table__.c.user_id
        assert col.nullable is False

    def test_user_id_foreign_key(self) -> None:
        col = AuthorizationCode.__table__.c.user_id
        fk = list(col.foreign_keys)[0]
        assert fk.column.table.name == "users"

    def test_client_id_indexed(self) -> None:
        col = AuthorizationCode.__table__.c.client_id
        assert col.index is True

    def test_client_id_not_nullable(self) -> None:
        col = AuthorizationCode.__table__.c.client_id
        assert col.nullable is False

    def test_nonce_nullable(self) -> None:
        col = AuthorizationCode.__table__.c.nonce
        assert col.nullable is True

    def test_pkce_fields_nullable(self) -> None:
        assert AuthorizationCode.__table__.c.code_challenge.nullable is True
        assert AuthorizationCode.__table__.c.code_challenge_method.nullable is True

    def test_expires_at_not_nullable(self) -> None:
        col = AuthorizationCode.__table__.c.expires_at
        assert col.nullable is False

    def test_used_at_nullable(self) -> None:
        col = AuthorizationCode.__table__.c.used_at
        assert col.nullable is True

    def test_is_used_default(self) -> None:
        col = AuthorizationCode.__table__.c.is_used
        assert col.default.arg is False
        assert col.nullable is False

    def test_pkce_fields_set(self) -> None:
        now = datetime.now(timezone.utc)
        ac = AuthorizationCode(
            code="pkce-code",
            user_id=uuid.uuid4(),
            client_id="spa-client",
            redirect_uri="https://spa.example.com/cb",
            code_challenge="E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
            code_challenge_method="S256",
            expires_at=now + timedelta(minutes=10),
        )
        assert ac.code_challenge is not None
        assert ac.code_challenge_method == "S256"

    def test_nonce_set(self) -> None:
        now = datetime.now(timezone.utc)
        ac = AuthorizationCode(
            code="nonce-code",
            user_id=uuid.uuid4(),
            client_id="oidc-client",
            redirect_uri="https://app.example.com/cb",
            nonce="random-nonce-value",
            expires_at=now + timedelta(minutes=10),
        )
        assert ac.nonce == "random-nonce-value"

    def test_repr(self) -> None:
        now = datetime.now(timezone.utc)
        ac = AuthorizationCode(
            code="abcdef123456",
            user_id=uuid.uuid4(),
            client_id="test-client",
            redirect_uri="https://app.example.com/cb",
            expires_at=now + timedelta(minutes=10),
        )
        r = repr(ac)
        assert "abcdef12" in r
        assert "test-client" in r

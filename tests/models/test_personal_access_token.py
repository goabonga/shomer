# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for PersonalAccessToken model."""

import uuid
from datetime import datetime, timezone

from shomer.models.personal_access_token import PAT_PREFIX, PersonalAccessToken


class TestPersonalAccessTokenModel:
    """Tests for PersonalAccessToken SQLAlchemy model definition."""

    def test_tablename(self) -> None:
        assert PersonalAccessToken.__tablename__ == "personal_access_tokens"

    def test_required_fields(self) -> None:
        uid = uuid.uuid4()
        pat = PersonalAccessToken(
            user_id=uid,
            name="CI deploy key",
            token_prefix="shm_pat_ab",
            token_hash="a" * 64,
            scopes="api:read api:write",
            is_revoked=False,
        )
        assert pat.user_id == uid
        assert pat.name == "CI deploy key"
        assert pat.token_prefix == "shm_pat_ab"
        assert pat.token_hash == "a" * 64
        assert pat.scopes == "api:read api:write"
        assert pat.is_revoked is False
        assert pat.expires_at is None
        assert pat.last_used_at is None

    def test_token_hash_unique(self) -> None:
        col = PersonalAccessToken.__table__.c.token_hash
        assert col.unique is True

    def test_token_hash_indexed(self) -> None:
        col = PersonalAccessToken.__table__.c.token_hash
        assert col.index is True

    def test_user_id_indexed(self) -> None:
        col = PersonalAccessToken.__table__.c.user_id
        assert col.index is True

    def test_with_expiration(self) -> None:
        now = datetime.now(timezone.utc)
        pat = PersonalAccessToken(
            user_id=uuid.uuid4(),
            name="temp key",
            token_prefix="shm_pat_cd",
            token_hash="b" * 64,
            scopes="",
            expires_at=now,
            is_revoked=False,
        )
        assert pat.expires_at == now

    def test_with_last_used(self) -> None:
        now = datetime.now(timezone.utc)
        pat = PersonalAccessToken(
            user_id=uuid.uuid4(),
            name="active key",
            token_prefix="shm_pat_ef",
            token_hash="c" * 64,
            scopes="api:read",
            last_used_at=now,
            is_revoked=False,
        )
        assert pat.last_used_at == now

    def test_pat_prefix_constant(self) -> None:
        assert PAT_PREFIX == "shm_pat_"

    def test_repr(self) -> None:
        pat = PersonalAccessToken(
            user_id=uuid.uuid4(),
            name="my-key",
            token_prefix="shm_pat_gh",
            token_hash="d" * 64,
            scopes="",
            is_revoked=False,
        )
        r = repr(pat)
        assert "my-key" in r
        assert "shm_pat_gh" in r

    def test_revoked_token(self) -> None:
        pat = PersonalAccessToken(
            user_id=uuid.uuid4(),
            name="revoked",
            token_prefix="shm_pat_ij",
            token_hash="e" * 64,
            scopes="",
            is_revoked=True,
        )
        assert pat.is_revoked is True

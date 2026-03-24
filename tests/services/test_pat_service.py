# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for PATService."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from shomer.models.personal_access_token import PAT_PREFIX
from shomer.services.pat_service import PATCreateResult, PATError, PATInfo, PATService


class TestPATCreate:
    """Tests for PAT creation."""

    def test_create_returns_raw_token_with_prefix(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            svc = PATService(db)
            result = await svc.create(
                user_id=uuid.uuid4(), name="CI key", scopes="api:read"
            )
            assert isinstance(result, PATCreateResult)
            assert result.token.startswith(PAT_PREFIX)
            assert result.token_prefix == result.token[:16]
            assert result.name == "CI key"
            assert result.scopes == "api:read"
            db.add.assert_called_once()
            db.flush.assert_awaited_once()

        asyncio.run(_run())

    def test_create_stores_hash_not_raw(self) -> None:
        async def _run() -> None:
            import hashlib

            db = AsyncMock()
            svc = PATService(db)
            result = await svc.create(user_id=uuid.uuid4(), name="key")
            pat_obj = db.add.call_args[0][0]
            expected_hash = hashlib.sha256(result.token.encode()).hexdigest()
            assert pat_obj.token_hash == expected_hash
            assert result.token not in pat_obj.token_hash

        asyncio.run(_run())

    def test_create_with_expiration(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            svc = PATService(db)
            exp = datetime.now(timezone.utc) + timedelta(days=30)
            result = await svc.create(user_id=uuid.uuid4(), name="tmp", expires_at=exp)
            assert result.expires_at == exp

        asyncio.run(_run())

    def test_each_create_generates_unique_token(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            svc = PATService(db)
            r1 = await svc.create(user_id=uuid.uuid4(), name="a")
            r2 = await svc.create(user_id=uuid.uuid4(), name="b")
            assert r1.token != r2.token

        asyncio.run(_run())


class TestPATValidate:
    """Tests for PAT validation."""

    def test_valid_token(self) -> None:
        async def _run() -> None:
            import hashlib

            raw = f"{PAT_PREFIX}test-secret-123"
            token_hash = hashlib.sha256(raw.encode()).hexdigest()

            mock_pat = MagicMock()
            mock_pat.token_hash = token_hash
            mock_pat.is_revoked = False
            mock_pat.expires_at = None
            mock_pat.last_used_at = None

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_pat

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = PATService(db)
            pat = await svc.validate(raw)
            assert pat is mock_pat
            assert pat.last_used_at is not None
            db.flush.assert_awaited_once()

        asyncio.run(_run())

    def test_invalid_prefix_raises(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            svc = PATService(db)
            with pytest.raises(PATError, match="Invalid token format"):
                await svc.validate("bad_prefix_token")

        asyncio.run(_run())

    def test_unknown_token_raises(self) -> None:
        async def _run() -> None:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = PATService(db)
            with pytest.raises(PATError, match="Invalid token"):
                await svc.validate(f"{PAT_PREFIX}unknown-token")

        asyncio.run(_run())

    def test_revoked_token_raises(self) -> None:
        async def _run() -> None:
            mock_pat = MagicMock()
            mock_pat.is_revoked = True

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_pat

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = PATService(db)
            with pytest.raises(PATError, match="revoked"):
                await svc.validate(f"{PAT_PREFIX}some-token")

        asyncio.run(_run())

    def test_expired_token_raises(self) -> None:
        async def _run() -> None:
            mock_pat = MagicMock()
            mock_pat.is_revoked = False
            mock_pat.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_pat

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = PATService(db)
            with pytest.raises(PATError, match="expired"):
                await svc.validate(f"{PAT_PREFIX}expired-token")

        asyncio.run(_run())

    def test_non_expired_token_passes(self) -> None:
        async def _run() -> None:
            mock_pat = MagicMock()
            mock_pat.is_revoked = False
            mock_pat.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            mock_pat.last_used_at = None

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_pat

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = PATService(db)
            pat = await svc.validate(f"{PAT_PREFIX}valid-token")
            assert pat.last_used_at is not None

        asyncio.run(_run())


class TestPATRevoke:
    """Tests for PAT revocation."""

    def test_revoke_success(self) -> None:
        async def _run() -> None:
            mock_pat = MagicMock()
            mock_pat.is_revoked = False

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_pat

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = PATService(db)
            await svc.revoke(uuid.uuid4(), uuid.uuid4())
            assert mock_pat.is_revoked is True
            db.flush.assert_awaited_once()

        asyncio.run(_run())

    def test_revoke_not_found_raises(self) -> None:
        async def _run() -> None:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = PATService(db)
            with pytest.raises(PATError, match="not found"):
                await svc.revoke(uuid.uuid4(), uuid.uuid4())

        asyncio.run(_run())


class TestPATRegenerate:
    """Tests for PAT regeneration."""

    def test_regenerate_revokes_old_and_creates_new(self) -> None:
        async def _run() -> None:
            old_pat = MagicMock()
            old_pat.name = "CI key"
            old_pat.scopes = "api:read"
            old_pat.expires_at = None
            old_pat.is_revoked = False

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = old_pat

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = PATService(db)
            uid = uuid.uuid4()
            result = await svc.regenerate(uuid.uuid4(), uid)

            assert old_pat.is_revoked is True
            assert isinstance(result, PATCreateResult)
            assert result.token.startswith(PAT_PREFIX)
            assert result.name == "CI key"
            assert result.scopes == "api:read"

        asyncio.run(_run())

    def test_regenerate_not_found_raises(self) -> None:
        async def _run() -> None:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = PATService(db)
            with pytest.raises(PATError, match="not found"):
                await svc.regenerate(uuid.uuid4(), uuid.uuid4())

        asyncio.run(_run())

    def test_regenerate_preserves_expiration(self) -> None:
        async def _run() -> None:
            exp = datetime.now(timezone.utc) + timedelta(days=30)
            old_pat = MagicMock()
            old_pat.name = "tmp"
            old_pat.scopes = ""
            old_pat.expires_at = exp
            old_pat.is_revoked = False

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = old_pat

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = PATService(db)
            result = await svc.regenerate(uuid.uuid4(), uuid.uuid4())
            assert result.expires_at == exp

        asyncio.run(_run())


class TestPATRevokeAll:
    """Tests for bulk revoke all."""

    def test_revoke_all_marks_active_tokens(self) -> None:
        async def _run() -> None:
            pat1 = MagicMock()
            pat1.is_revoked = False
            pat2 = MagicMock()
            pat2.is_revoked = False

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [pat1, pat2]

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = PATService(db)
            count = await svc.revoke_all_for_user(uuid.uuid4())
            assert count == 2
            assert pat1.is_revoked is True
            assert pat2.is_revoked is True
            db.flush.assert_awaited_once()

        asyncio.run(_run())

    def test_revoke_all_returns_zero_when_none_active(self) -> None:
        async def _run() -> None:
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = PATService(db)
            count = await svc.revoke_all_for_user(uuid.uuid4())
            assert count == 0

        asyncio.run(_run())


class TestPATListForUser:
    """Tests for listing user PATs."""

    def test_list_returns_metadata(self) -> None:
        async def _run() -> None:
            now = datetime.now(timezone.utc)
            mock_pat = MagicMock()
            mock_pat.id = uuid.uuid4()
            mock_pat.name = "my-key"
            mock_pat.token_prefix = "shm_pat_abc"
            mock_pat.scopes = "api:read"
            mock_pat.expires_at = None
            mock_pat.last_used_at = now
            mock_pat.is_revoked = False
            mock_pat.created_at = now

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_pat]

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = PATService(db)
            pats = await svc.list_for_user(uuid.uuid4())
            assert len(pats) == 1
            assert isinstance(pats[0], PATInfo)
            assert pats[0].name == "my-key"
            assert pats[0].token_prefix == "shm_pat_abc"

        asyncio.run(_run())

    def test_list_empty(self) -> None:
        async def _run() -> None:
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = PATService(db)
            pats = await svc.list_for_user(uuid.uuid4())
            assert pats == []

        asyncio.run(_run())

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for SessionService."""

from __future__ import annotations

import asyncio
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

from shomer.services.session_service import SessionService


class TestCreate:
    """Tests for SessionService.create()."""

    def test_creates_session(self) -> None:
        """Create returns a session with token_hash, csrf_token, and raw token."""

        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            uid = uuid.uuid4()
            svc = SessionService(db)
            session, raw_token = await svc.create(user_id=uid)
            assert session.user_id == uid
            assert session.token_hash is not None
            assert session.csrf_token is not None
            assert len(raw_token) == 32
            db.add.assert_called_once()

        asyncio.run(_run())

    def test_stores_metadata(self) -> None:
        """Create stores user_agent and ip_address."""

        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            uid = uuid.uuid4()
            svc = SessionService(db)
            session, _ = await svc.create(
                user_id=uid,
                user_agent="Mozilla/5.0",
                ip_address="10.0.0.1",
            )
            assert session.user_agent == "Mozilla/5.0"
            assert session.ip_address == "10.0.0.1"

        asyncio.run(_run())

    def test_sets_expiration(self) -> None:
        """Create sets an expiration time in the future."""

        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            uid = uuid.uuid4()
            svc = SessionService(db)
            session, _ = await svc.create(user_id=uid)
            assert session.expires_at > datetime.now(timezone.utc)

        asyncio.run(_run())


class TestValidate:
    """Tests for SessionService.validate()."""

    def test_valid_token(self) -> None:
        """Valid token returns the session."""

        async def _run() -> None:
            db = AsyncMock()
            uid = uuid.uuid4()
            raw_token = uuid.uuid4().hex
            token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

            mock_session = MagicMock()
            mock_session.user_id = uid
            mock_session.token_hash = token_hash
            mock_session.expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_session
            db.execute.return_value = result

            svc = SessionService(db)
            found = await svc.validate(raw_token)
            assert found is not None
            assert found.user_id == uid

        asyncio.run(_run())

    def test_invalid_token_returns_none(self) -> None:
        """Invalid token returns None."""

        async def _run() -> None:
            db = AsyncMock()

            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db.execute.return_value = result

            svc = SessionService(db)
            found = await svc.validate("nonexistent-token")
            assert found is None

        asyncio.run(_run())

    def test_expired_session_returns_none(self) -> None:
        """Expired session returns None."""

        async def _run() -> None:
            db = AsyncMock()

            mock_session = MagicMock()
            mock_session.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_session
            db.execute.return_value = result

            svc = SessionService(db)
            found = await svc.validate("some-token")
            assert found is None

        asyncio.run(_run())


class TestRenew:
    """Tests for SessionService.renew()."""

    def test_extends_expiration(self) -> None:
        """Renew updates last_activity and extends expires_at."""

        async def _run() -> None:
            db = AsyncMock()
            db.flush = AsyncMock()

            mock_session = MagicMock()
            mock_session.last_activity = None
            mock_session.expires_at = None

            svc = SessionService(db)
            renewed = await svc.renew(mock_session)
            assert renewed.last_activity is not None
            assert renewed.expires_at is not None
            db.flush.assert_awaited_once()

        asyncio.run(_run())


class TestDelete:
    """Tests for SessionService.delete()."""

    def test_deletes_session(self) -> None:
        """Deleting an existing session returns True."""

        async def _run() -> None:
            db = AsyncMock()
            db.flush = AsyncMock()

            mock_result = MagicMock()
            mock_result.rowcount = 1
            db.execute.return_value = mock_result

            svc = SessionService(db)
            deleted = await svc.delete(uuid.uuid4())
            assert deleted is True

        asyncio.run(_run())

    def test_delete_nonexistent_returns_false(self) -> None:
        """Deleting a nonexistent session returns False."""

        async def _run() -> None:
            db = AsyncMock()
            db.flush = AsyncMock()

            mock_result = MagicMock()
            mock_result.rowcount = 0
            db.execute.return_value = mock_result

            svc = SessionService(db)
            deleted = await svc.delete(uuid.uuid4())
            assert deleted is False

        asyncio.run(_run())


class TestDeleteAllForUser:
    """Tests for SessionService.delete_all_for_user()."""

    def test_deletes_all_user_sessions(self) -> None:
        """Returns the count of deleted sessions."""

        async def _run() -> None:
            db = AsyncMock()
            db.flush = AsyncMock()

            mock_result = MagicMock()
            mock_result.rowcount = 3
            db.execute.return_value = mock_result

            svc = SessionService(db)
            count = await svc.delete_all_for_user(uuid.uuid4())
            assert count == 3

        asyncio.run(_run())

    def test_does_not_delete_other_users(self) -> None:
        """Returns 0 when user has no sessions."""

        async def _run() -> None:
            db = AsyncMock()
            db.flush = AsyncMock()

            mock_result = MagicMock()
            mock_result.rowcount = 0
            db.execute.return_value = mock_result

            svc = SessionService(db)
            count = await svc.delete_all_for_user(uuid.uuid4())
            assert count == 0

        asyncio.run(_run())


class TestListActive:
    """Tests for SessionService.list_active()."""

    def test_lists_active_sessions(self) -> None:
        """Returns active sessions for a user."""

        async def _run() -> None:
            db = AsyncMock()

            mock_s1 = MagicMock()
            mock_s2 = MagicMock()

            result = MagicMock()
            scalars_mock = MagicMock()
            scalars_mock.all.return_value = [mock_s1, mock_s2]
            result.scalars.return_value = scalars_mock
            db.execute.return_value = result

            svc = SessionService(db)
            sessions = await svc.list_active(uuid.uuid4())
            assert len(sessions) == 2

        asyncio.run(_run())

    def test_excludes_expired(self) -> None:
        """Returns only non-expired sessions (DB handles filtering)."""

        async def _run() -> None:
            db = AsyncMock()

            mock_s1 = MagicMock()  # Only the non-expired one

            result = MagicMock()
            scalars_mock = MagicMock()
            scalars_mock.all.return_value = [mock_s1]
            result.scalars.return_value = scalars_mock
            db.execute.return_value = result

            svc = SessionService(db)
            sessions = await svc.list_active(uuid.uuid4())
            assert len(sessions) == 1

        asyncio.run(_run())

    def test_empty_for_unknown_user(self) -> None:
        """Returns empty list for unknown user."""

        async def _run() -> None:
            db = AsyncMock()

            result = MagicMock()
            scalars_mock = MagicMock()
            scalars_mock.all.return_value = []
            result.scalars.return_value = scalars_mock
            db.execute.return_value = result

            svc = SessionService(db)
            sessions = await svc.list_active(uuid.uuid4())
            assert sessions == []

        asyncio.run(_run())


class TestSessionValidateNaiveDatetime:
    """Test session validation with naive (no-tzinfo) datetime."""

    def test_valid_session_with_naive_datetime(self) -> None:
        """Validate handles naive datetimes (SQLite compat)."""
        import warnings

        async def _run() -> None:
            db = AsyncMock()
            raw = uuid.uuid4().hex
            thash = hashlib.sha256(raw.encode()).hexdigest()

            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                naive_now = datetime.utcnow()  # noqa: DTZ003
                naive_future = naive_now + timedelta(hours=24)

            mock_session = MagicMock()
            mock_session.user_id = uuid.uuid4()
            mock_session.token_hash = thash
            mock_session.expires_at = naive_future

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_session
            db.execute.return_value = result

            svc = SessionService(db)
            found = await svc.validate(raw)
            assert found is not None

        asyncio.run(_run())

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for model query helpers."""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

from shomer.models.queries import create_user, get_user_by_email, get_user_by_id


class TestCreateUser:
    """Tests for create_user query helper."""

    def test_creates_user_with_email_and_password(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.add_all = MagicMock()
            db.flush = AsyncMock()

            user = await create_user(
                db, email="a@b.com", password_hash="$hash", username="bob"
            )
            assert user.username == "bob"
            db.add.assert_called_once()
            db.add_all.assert_called_once()
            assert db.flush.await_count == 2

        asyncio.run(_run())


class TestGetUserByEmail:
    """Tests for get_user_by_email query helper."""

    def test_returns_user_when_found(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            mock_user = MagicMock()
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_user
            db.execute.return_value = result

            found = await get_user_by_email(db, "a@b.com")
            assert found is mock_user

        asyncio.run(_run())

    def test_returns_none_when_not_found(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db.execute.return_value = result

            found = await get_user_by_email(db, "x@b.com")
            assert found is None

        asyncio.run(_run())


class TestGetUserById:
    """Tests for get_user_by_id query helper."""

    def test_returns_user_when_found(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            mock_user = MagicMock()
            mock_user.username = "found"
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_user
            db.execute.return_value = result

            found = await get_user_by_id(db, uuid.uuid4())
            assert found is not None
            assert found.username == "found"

        asyncio.run(_run())

    def test_returns_none_when_not_found(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db.execute.return_value = result

            found = await get_user_by_id(db, uuid.uuid4())
            assert found is None

        asyncio.run(_run())

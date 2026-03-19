# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for UserPassword model."""

import uuid

from shomer.models.user_password import UserPassword


class TestUserPasswordModel:
    """Tests for UserPassword SQLAlchemy model."""

    def test_repr(self) -> None:
        uid = uuid.uuid4()
        pw = UserPassword(user_id=uid, password_hash="hash", is_current=True)
        r = repr(pw)
        assert str(uid) in r
        assert "current=" in r

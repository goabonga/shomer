# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for User model."""

from shomer.models.user import User


class TestUserModel:
    """Tests for User SQLAlchemy model."""

    def test_repr(self) -> None:
        user = User(username="test", is_active=True)
        r = repr(user)
        assert "User" in r
        assert "active=" in r

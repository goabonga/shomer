# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for UserEmail model."""

import uuid

from shomer.models.user_email import UserEmail


class TestUserEmailModel:
    """Tests for UserEmail SQLAlchemy model."""

    def test_repr(self) -> None:
        ue = UserEmail(
            user_id=uuid.uuid4(),
            email="test@example.com",
            is_verified=True,
        )
        r = repr(ue)
        assert "test@example.com" in r
        assert "verified=" in r

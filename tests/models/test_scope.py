# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for Scope model."""

from shomer.models.scope import Scope


class TestScopeModel:
    """Tests for Scope SQLAlchemy model definition."""

    def test_tablename(self) -> None:
        assert Scope.__tablename__ == "scopes"

    def test_required_fields(self) -> None:
        s = Scope(name="admin:users:read", description="Read users")
        assert s.name == "admin:users:read"
        assert s.description == "Read users"

    def test_name_unique(self) -> None:
        col = Scope.__table__.c.name
        assert col.unique is True

    def test_name_indexed(self) -> None:
        col = Scope.__table__.c.name
        assert col.index is True

    def test_description_nullable(self) -> None:
        s = Scope(name="test:scope")
        assert s.description is None

    def test_repr(self) -> None:
        s = Scope(name="api:orders:write")
        r = repr(s)
        assert "api:orders:write" in r

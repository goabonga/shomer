# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for Role model."""

from shomer.models.role import Role


class TestRoleModel:
    """Tests for Role SQLAlchemy model definition."""

    def test_tablename(self) -> None:
        assert Role.__tablename__ == "roles"

    def test_required_fields(self) -> None:
        r = Role(name="admin", description="Administrator", is_system=True)
        assert r.name == "admin"
        assert r.description == "Administrator"
        assert r.is_system is True

    def test_name_unique(self) -> None:
        col = Role.__table__.c.name
        assert col.unique is True

    def test_name_indexed(self) -> None:
        col = Role.__table__.c.name
        assert col.index is True

    def test_description_nullable(self) -> None:
        r = Role(name="editor")
        assert r.description is None

    def test_repr(self) -> None:
        r = Role(name="viewer", is_system=False)
        rep = repr(r)
        assert "viewer" in rep
        assert "False" in rep

    def test_repr_system(self) -> None:
        r = Role(name="superadmin", is_system=True)
        rep = repr(r)
        assert "superadmin" in rep
        assert "True" in rep

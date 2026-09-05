# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""Tests for the ORM models."""

from shomer_lib.models import Base, Client, User


def test_metadata_names_its_constraints() -> None:
    # Deterministic names are what keep Alembic from reporting a diff on
    # constraints nobody touched.
    assert Base.metadata.naming_convention["pk"] == "pk_%(table_name)s"
    assert set(Base.metadata.tables) == {"users", "clients"}


def test_user_columns() -> None:
    columns = User.__table__.columns
    assert columns["subject"].primary_key
    assert columns["email"].unique
    assert "password" not in columns


def test_client_accepts_a_registered_redirect_uri() -> None:
    client = Client(
        client_id="app",
        name="App",
        redirect_uris="https://app.example.test/callback\nhttps://app.example.test/alt",
        created_at=0.0,
    )
    assert client.allows("https://app.example.test/callback")
    assert client.allows("https://app.example.test/alt")


def test_client_rejects_a_prefix_of_a_registered_uri() -> None:
    # A prefix match on `https://app.example.test/` would also accept
    # `https://app.example.test.attacker.test/`, which is how an
    # authorization code leaves for someone else's server.
    client = Client(
        client_id="app",
        name="App",
        redirect_uris="https://app.example.test/callback",
        created_at=0.0,
    )
    assert not client.allows("https://app.example.test/callback/../evil")
    assert not client.allows("https://app.example.test.attacker.test/callback")
    assert not client.allows("")

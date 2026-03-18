# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for UserProfile model."""

import uuid

from shomer.models.user import User  # noqa: F401 — register mapper
from shomer.models.user_email import UserEmail  # noqa: F401 — register mapper
from shomer.models.user_password import UserPassword  # noqa: F401 — register mapper
from shomer.models.user_profile import UserProfile


class TestUserProfileModel:
    """Tests for UserProfile SQLAlchemy model definition."""

    def test_tablename(self) -> None:
        assert UserProfile.__tablename__ == "user_profiles"

    def test_phone_number_verified_column(self) -> None:
        col = UserProfile.__table__.c.phone_number_verified
        assert col.nullable is False
        assert col.default.arg is False

    def test_nullable_claim_fields(self) -> None:
        profile = UserProfile(user_id=uuid.uuid4())
        assert profile.name is None
        assert profile.given_name is None
        assert profile.family_name is None
        assert profile.middle_name is None
        assert profile.nickname is None
        assert profile.preferred_username is None
        assert profile.profile_url is None
        assert profile.picture_url is None
        assert profile.website is None
        assert profile.gender is None
        assert profile.birthdate is None
        assert profile.zoneinfo is None
        assert profile.locale is None

    def test_nullable_address_fields(self) -> None:
        profile = UserProfile(user_id=uuid.uuid4())
        assert profile.address_formatted is None
        assert profile.address_street is None
        assert profile.address_locality is None
        assert profile.address_region is None
        assert profile.address_postal_code is None
        assert profile.address_country is None

    def test_nullable_phone_fields(self) -> None:
        profile = UserProfile(user_id=uuid.uuid4())
        assert profile.phone_number is None

    def test_set_claim_fields(self) -> None:
        profile = UserProfile(
            user_id=uuid.uuid4(),
            name="Jane Doe",
            given_name="Jane",
            family_name="Doe",
            nickname="jdoe",
            locale="en-US",
            zoneinfo="America/New_York",
            birthdate="1990-01-15",
            gender="female",
            website="https://example.com",
        )
        assert profile.name == "Jane Doe"
        assert profile.given_name == "Jane"
        assert profile.family_name == "Doe"
        assert profile.nickname == "jdoe"
        assert profile.locale == "en-US"
        assert profile.zoneinfo == "America/New_York"
        assert profile.birthdate == "1990-01-15"
        assert profile.gender == "female"
        assert profile.website == "https://example.com"

    def test_set_address_fields(self) -> None:
        profile = UserProfile(
            user_id=uuid.uuid4(),
            address_formatted="123 Main St, Springfield, IL 62704, US",
            address_street="123 Main St",
            address_locality="Springfield",
            address_region="IL",
            address_postal_code="62704",
            address_country="US",
        )
        assert profile.address_street == "123 Main St"
        assert profile.address_locality == "Springfield"
        assert profile.address_region == "IL"
        assert profile.address_postal_code == "62704"
        assert profile.address_country == "US"

    def test_repr(self) -> None:
        uid = uuid.uuid4()
        profile = UserProfile(user_id=uid, name="Test")
        assert f"user_id={uid}" in repr(profile)
        assert "name=Test" in repr(profile)

    def test_user_id_column_is_required(self) -> None:
        col = UserProfile.__table__.c.user_id
        assert col.nullable is False

    def test_user_id_column_is_unique(self) -> None:
        col = UserProfile.__table__.c.user_id
        assert col.unique is True

    def test_user_id_column_is_indexed(self) -> None:
        col = UserProfile.__table__.c.user_id
        assert col.index is True

    def test_user_id_foreign_key(self) -> None:
        col = UserProfile.__table__.c.user_id
        fk = list(col.foreign_keys)[0]
        assert fk.column.table.name == "users"
        assert fk.column.name == "id"


class TestUserProfileRelationship:
    """Tests for UserProfile ↔ User relationship configuration."""

    def test_user_relationship_exists(self) -> None:
        rel = UserProfile.__mapper__.relationships["user"]
        assert rel.back_populates == "profile"

    def test_user_model_has_profile_relationship(self) -> None:

        rel = User.__mapper__.relationships["profile"]
        assert rel.back_populates == "user"
        assert rel.uselist is False

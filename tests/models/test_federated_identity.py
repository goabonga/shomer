# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for FederatedIdentity model."""

import uuid
from datetime import datetime, timezone

from shomer.models.federated_identity import FederatedIdentity


class TestFederatedIdentityModel:
    """Tests for FederatedIdentity SQLAlchemy model definition."""

    def test_tablename(self) -> None:
        assert FederatedIdentity.__tablename__ == "federated_identities"

    def test_required_fields(self) -> None:
        uid = uuid.uuid4()
        pid = uuid.uuid4()
        now = datetime.now(timezone.utc)
        fi = FederatedIdentity(
            user_id=uid,
            identity_provider_id=pid,
            external_subject="google-12345",
            linked_at=now,
        )
        assert fi.user_id == uid
        assert fi.identity_provider_id == pid
        assert fi.external_subject == "google-12345"
        assert fi.linked_at == now
        assert fi.external_email is None
        assert fi.external_username is None
        assert fi.raw_claims is None
        assert fi.last_login_at is None

    def test_full_fields(self) -> None:
        now = datetime.now(timezone.utc)
        fi = FederatedIdentity(
            user_id=uuid.uuid4(),
            identity_provider_id=uuid.uuid4(),
            external_subject="sub-abc",
            external_email="user@acme.com",
            external_username="johndoe",
            raw_claims={"sub": "sub-abc", "email": "user@acme.com", "name": "John"},
            linked_at=now,
            last_login_at=now,
        )
        assert fi.external_email == "user@acme.com"
        assert fi.external_username == "johndoe"
        assert fi.raw_claims is not None
        assert fi.raw_claims["name"] == "John"
        assert fi.last_login_at == now

    def test_unique_constraint(self) -> None:
        names = [
            c.name for c in getattr(FederatedIdentity.__table__, "constraints", [])
        ]
        assert "uq_federated_identities_idp_subject" in names

    def test_user_id_indexed(self) -> None:
        col = FederatedIdentity.__table__.c.user_id
        assert col.index is True

    def test_identity_provider_id_indexed(self) -> None:
        col = FederatedIdentity.__table__.c.identity_provider_id
        assert col.index is True

    def test_repr(self) -> None:
        uid = uuid.uuid4()
        pid = uuid.uuid4()
        fi = FederatedIdentity(
            user_id=uid,
            identity_provider_id=pid,
            external_subject="ext-123",
            linked_at=datetime.now(timezone.utc),
        )
        r = repr(fi)
        assert str(uid) in r
        assert str(pid) in r
        assert "ext-123" in r

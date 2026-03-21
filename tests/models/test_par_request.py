# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for PARRequest model."""

from datetime import datetime, timezone

from shomer.models.par_request import PARRequest


class TestPARRequestModel:
    """Tests for PARRequest SQLAlchemy model definition."""

    def test_tablename(self) -> None:
        assert PARRequest.__tablename__ == "par_requests"

    def test_required_fields(self) -> None:
        now = datetime.now(timezone.utc)
        par = PARRequest(
            request_uri="urn:ietf:params:oauth:request_uri:abc123",
            client_id="my-client",
            parameters={"response_type": "code", "scope": "openid"},
            expires_at=now,
        )
        assert par.request_uri == "urn:ietf:params:oauth:request_uri:abc123"
        assert par.client_id == "my-client"
        assert par.parameters["response_type"] == "code"
        assert par.expires_at == now

    def test_request_uri_unique(self) -> None:
        col = PARRequest.__table__.c.request_uri
        assert col.unique is True

    def test_request_uri_indexed(self) -> None:
        col = PARRequest.__table__.c.request_uri
        assert col.index is True

    def test_parameters_is_json(self) -> None:
        par = PARRequest(
            request_uri="urn:test",
            client_id="c",
            parameters={"key": "value", "list": [1, 2]},
            expires_at=datetime.now(timezone.utc),
        )
        assert par.parameters["list"] == [1, 2]

    def test_repr(self) -> None:
        par = PARRequest(
            request_uri="urn:ietf:params:oauth:request_uri:xyz789",
            client_id="my-app",
            parameters={},
            expires_at=datetime.now(timezone.utc),
        )
        r = repr(par)
        assert "urn:ietf:params:oauth:request_uri:xyz789" in r
        assert "my-app" in r

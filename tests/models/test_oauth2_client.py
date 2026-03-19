# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for OAuth2Client model."""

from shomer.models.oauth2_client import ClientType, OAuth2Client


class TestClientType:
    """Tests for ClientType enum."""

    def test_confidential_value(self) -> None:
        assert ClientType.CONFIDENTIAL.value == "confidential"

    def test_public_value(self) -> None:
        assert ClientType.PUBLIC.value == "public"

    def test_is_str_enum(self) -> None:
        assert isinstance(ClientType.CONFIDENTIAL, str)


class TestOAuth2ClientModel:
    """Tests for OAuth2Client SQLAlchemy model definition."""

    def test_tablename(self) -> None:
        assert OAuth2Client.__tablename__ == "oauth2_clients"

    def test_required_fields(self) -> None:
        client = OAuth2Client(
            client_id="my-app",
            client_name="My App",
        )
        assert client.client_id == "my-app"
        assert client.client_name == "My App"

    def test_client_id_unique(self) -> None:
        col = OAuth2Client.__table__.c.client_id
        assert col.unique is True

    def test_client_id_indexed(self) -> None:
        col = OAuth2Client.__table__.c.client_id
        assert col.index is True

    def test_client_id_not_nullable(self) -> None:
        col = OAuth2Client.__table__.c.client_id
        assert col.nullable is False

    def test_client_secret_hash_nullable(self) -> None:
        col = OAuth2Client.__table__.c.client_secret_hash
        assert col.nullable is True

    def test_client_type_default(self) -> None:
        col = OAuth2Client.__table__.c.client_type
        assert col.default.arg is ClientType.CONFIDENTIAL

    def test_client_type_not_nullable(self) -> None:
        col = OAuth2Client.__table__.c.client_type
        assert col.nullable is False

    def test_is_active_default(self) -> None:
        col = OAuth2Client.__table__.c.is_active
        assert col.default.arg is True

    def test_redirect_uris_not_nullable(self) -> None:
        col = OAuth2Client.__table__.c.redirect_uris
        assert col.nullable is False

    def test_grant_types_not_nullable(self) -> None:
        col = OAuth2Client.__table__.c.grant_types
        assert col.nullable is False

    def test_response_types_not_nullable(self) -> None:
        col = OAuth2Client.__table__.c.response_types
        assert col.nullable is False

    def test_scopes_not_nullable(self) -> None:
        col = OAuth2Client.__table__.c.scopes
        assert col.nullable is False

    def test_oidc_metadata_nullable(self) -> None:
        assert OAuth2Client.__table__.c.logo_uri.nullable is True
        assert OAuth2Client.__table__.c.tos_uri.nullable is True
        assert OAuth2Client.__table__.c.policy_uri.nullable is True

    def test_contacts_not_nullable(self) -> None:
        col = OAuth2Client.__table__.c.contacts
        assert col.nullable is False

    def test_repr_confidential(self) -> None:
        client = OAuth2Client(
            client_id="test-app",
            client_name="Test",
            client_type=ClientType.CONFIDENTIAL,
        )
        r = repr(client)
        assert "client_id=test-app" in r
        assert "type=confidential" in r

    def test_repr_public(self) -> None:
        client = OAuth2Client(
            client_id="spa",
            client_name="SPA",
            client_type=ClientType.PUBLIC,
        )
        assert "type=public" in repr(client)

    def test_all_fields(self) -> None:
        client = OAuth2Client(
            client_id="full-app",
            client_name="Full App",
            client_secret_hash="hashed",
            client_type=ClientType.CONFIDENTIAL,
            redirect_uris=["https://app.example.com/callback"],
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
            scopes=["openid", "profile", "email"],
            logo_uri="https://app.example.com/logo.png",
            tos_uri="https://app.example.com/tos",
            policy_uri="https://app.example.com/privacy",
            contacts=["admin@example.com"],
        )
        assert client.client_secret_hash == "hashed"
        assert client.redirect_uris == ["https://app.example.com/callback"]
        assert client.grant_types == ["authorization_code", "refresh_token"]
        assert client.response_types == ["code"]
        assert client.scopes == ["openid", "profile", "email"]
        assert client.logo_uri == "https://app.example.com/logo.png"
        assert client.contacts == ["admin@example.com"]

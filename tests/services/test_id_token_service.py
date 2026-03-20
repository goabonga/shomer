# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for OIDC ID Token generation service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock

import jwt as pyjwt

from shomer.services.id_token_service import IDTokenService


def _settings() -> MagicMock:
    s = MagicMock()
    s.jwt_issuer = "https://auth.shomer.local"
    s.jwt_id_token_exp = 3600
    s.jwk_encryption_key = "test-key-that-is-at-least-32-bytes-long!"
    return s


def _decode(token: str, key: str) -> dict[str, Any]:
    return pyjwt.decode(token, key, algorithms=["HS256"], audience="client-1")


class TestRequiredClaims:
    """ID Token contains required OIDC claims."""

    def test_iss_sub_aud_exp_iat(self) -> None:
        settings = _settings()
        svc = IDTokenService(settings)
        token = svc.build_id_token(sub="user-1", aud="client-1")
        payload = _decode(token, settings.jwk_encryption_key)
        assert payload["iss"] == "https://auth.shomer.local"
        assert payload["sub"] == "user-1"
        assert payload["aud"] == "client-1"
        assert "exp" in payload
        assert "iat" in payload


class TestNonce:
    """Nonce handling in ID Token."""

    def test_nonce_included_when_provided(self) -> None:
        settings = _settings()
        svc = IDTokenService(settings)
        token = svc.build_id_token(sub="u", aud="client-1", nonce="abc123")
        payload = _decode(token, settings.jwk_encryption_key)
        assert payload["nonce"] == "abc123"

    def test_nonce_absent_when_not_provided(self) -> None:
        settings = _settings()
        svc = IDTokenService(settings)
        token = svc.build_id_token(sub="u", aud="client-1")
        payload = _decode(token, settings.jwk_encryption_key)
        assert "nonce" not in payload


class TestAuthTime:
    """auth_time claim in ID Token."""

    def test_auth_time_included(self) -> None:
        settings = _settings()
        svc = IDTokenService(settings)
        auth_t = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        token = svc.build_id_token(sub="u", aud="client-1", auth_time=auth_t)
        payload = _decode(token, settings.jwk_encryption_key)
        assert payload["auth_time"] == int(auth_t.timestamp())

    def test_auth_time_absent_when_not_provided(self) -> None:
        settings = _settings()
        svc = IDTokenService(settings)
        token = svc.build_id_token(sub="u", aud="client-1")
        payload = _decode(token, settings.jwk_encryption_key)
        assert "auth_time" not in payload


class TestEmailScope:
    """Email claims based on email scope."""

    def test_email_included_with_email_scope(self) -> None:
        settings = _settings()
        svc = IDTokenService(settings)
        token = svc.build_id_token(
            sub="u",
            aud="client-1",
            scopes=["openid", "email"],
            email="user@example.com",
            email_verified=True,
        )
        payload = _decode(token, settings.jwk_encryption_key)
        assert payload["email"] == "user@example.com"
        assert payload["email_verified"] is True

    def test_email_absent_without_email_scope(self) -> None:
        settings = _settings()
        svc = IDTokenService(settings)
        token = svc.build_id_token(
            sub="u",
            aud="client-1",
            scopes=["openid"],
            email="user@example.com",
        )
        payload = _decode(token, settings.jwk_encryption_key)
        assert "email" not in payload


class TestProfileScope:
    """Profile claims based on profile scope."""

    def test_profile_claims_included(self) -> None:
        settings = _settings()
        svc = IDTokenService(settings)
        profile = MagicMock()
        profile.name = "John Doe"
        profile.given_name = "John"
        profile.family_name = "Doe"
        profile.middle_name = None
        profile.nickname = "johnny"
        profile.preferred_username = "johndoe"
        profile.profile_url = "https://example.com/john"
        profile.picture_url = "https://example.com/john.jpg"
        profile.website = None
        profile.gender = "male"
        profile.birthdate = "1990-01-15"
        profile.zoneinfo = "Europe/Paris"
        profile.locale = "fr-FR"

        token = svc.build_id_token(
            sub="u",
            aud="client-1",
            scopes=["openid", "profile"],
            profile=profile,
        )
        payload = _decode(token, settings.jwk_encryption_key)
        assert payload["name"] == "John Doe"
        assert payload["given_name"] == "John"
        assert payload["family_name"] == "Doe"
        assert "middle_name" not in payload  # None values excluded
        assert payload["nickname"] == "johnny"
        assert payload["picture"] == "https://example.com/john.jpg"
        assert payload["gender"] == "male"
        assert payload["locale"] == "fr-FR"

    def test_profile_absent_without_scope(self) -> None:
        settings = _settings()
        svc = IDTokenService(settings)
        profile = MagicMock()
        profile.name = "John Doe"

        token = svc.build_id_token(
            sub="u",
            aud="client-1",
            scopes=["openid"],
            profile=profile,
        )
        payload = _decode(token, settings.jwk_encryption_key)
        assert "name" not in payload

    def test_profile_absent_when_no_profile_object(self) -> None:
        settings = _settings()
        svc = IDTokenService(settings)
        token = svc.build_id_token(
            sub="u",
            aud="client-1",
            scopes=["openid", "profile"],
            profile=None,
        )
        payload = _decode(token, settings.jwk_encryption_key)
        assert "name" not in payload


class TestAddressScope:
    """Address claims based on address scope."""

    def test_address_included(self) -> None:
        settings = _settings()
        svc = IDTokenService(settings)
        profile = MagicMock()
        profile.address_formatted = "123 Main St, Paris, France"
        profile.address_street = "123 Main St"
        profile.address_locality = "Paris"
        profile.address_region = "Île-de-France"
        profile.address_postal_code = "75001"
        profile.address_country = "France"

        token = svc.build_id_token(
            sub="u",
            aud="client-1",
            scopes=["openid", "address"],
            profile=profile,
        )
        payload = _decode(token, settings.jwk_encryption_key)
        assert "address" in payload
        addr = payload["address"]
        assert addr["formatted"] == "123 Main St, Paris, France"
        assert addr["locality"] == "Paris"
        assert addr["country"] == "France"

    def test_address_absent_when_empty(self) -> None:
        settings = _settings()
        svc = IDTokenService(settings)
        profile = MagicMock()
        profile.address_formatted = None
        profile.address_street = None
        profile.address_locality = None
        profile.address_region = None
        profile.address_postal_code = None
        profile.address_country = None

        token = svc.build_id_token(
            sub="u",
            aud="client-1",
            scopes=["openid", "address"],
            profile=profile,
        )
        payload = _decode(token, settings.jwk_encryption_key)
        assert "address" not in payload


class TestPhoneScope:
    """Phone claims based on phone scope."""

    def test_phone_included(self) -> None:
        settings = _settings()
        svc = IDTokenService(settings)
        profile = MagicMock()
        profile.phone_number = "+33612345678"
        profile.phone_number_verified = True

        token = svc.build_id_token(
            sub="u",
            aud="client-1",
            scopes=["openid", "phone"],
            profile=profile,
        )
        payload = _decode(token, settings.jwk_encryption_key)
        assert payload["phone_number"] == "+33612345678"
        assert payload["phone_number_verified"] is True

    def test_phone_absent_when_no_number(self) -> None:
        settings = _settings()
        svc = IDTokenService(settings)
        profile = MagicMock()
        profile.phone_number = None

        token = svc.build_id_token(
            sub="u",
            aud="client-1",
            scopes=["openid", "phone"],
            profile=profile,
        )
        payload = _decode(token, settings.jwk_encryption_key)
        assert "phone_number" not in payload


class TestAllScopes:
    """Multiple scopes combined."""

    def test_all_scopes_combined(self) -> None:
        settings = _settings()
        svc = IDTokenService(settings)
        profile = MagicMock()
        profile.name = "Jane"
        profile.given_name = None
        profile.family_name = None
        profile.middle_name = None
        profile.nickname = None
        profile.preferred_username = None
        profile.profile_url = None
        profile.picture_url = None
        profile.website = None
        profile.gender = None
        profile.birthdate = None
        profile.zoneinfo = None
        profile.locale = None
        profile.address_formatted = "1 Rue"
        profile.address_street = None
        profile.address_locality = None
        profile.address_region = None
        profile.address_postal_code = None
        profile.address_country = None
        profile.phone_number = "+1234"
        profile.phone_number_verified = False

        token = svc.build_id_token(
            sub="u",
            aud="client-1",
            nonce="n1",
            auth_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            scopes=["openid", "profile", "email", "address", "phone"],
            profile=profile,
            email="jane@example.com",
            email_verified=True,
        )
        payload = _decode(token, settings.jwk_encryption_key)
        assert payload["name"] == "Jane"
        assert payload["email"] == "jane@example.com"
        assert payload["address"]["formatted"] == "1 Rue"
        assert payload["phone_number"] == "+1234"
        assert payload["nonce"] == "n1"
        assert "auth_time" in payload

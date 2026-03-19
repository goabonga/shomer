# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for JWT validation service."""

from __future__ import annotations

import asyncio
import base64
import json
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import jwt as pyjwt
from cryptography.hazmat.primitives.asymmetric import rsa

from shomer.services.jwt_validation_service import (
    JWTValidationService,
    TokenError,
)

_ISSUER = "https://test.shomer.local"


def _settings(**overrides: object) -> MagicMock:
    """Create a mock Settings object."""
    s = MagicMock()
    s.jwt_issuer = overrides.get("jwt_issuer", _ISSUER)
    s.jwt_clock_skew = overrides.get("jwt_clock_skew", 5)
    return s


def _generate_rsa_pair() -> tuple[rsa.RSAPrivateKey, str, str]:
    """Generate an RSA key pair.

    Returns
    -------
    tuple[rsa.RSAPrivateKey, str, str]
        (private_key, public_jwk_json_str, kid)
    """
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub = private_key.public_key().public_numbers()
    n_bytes = pub.n.to_bytes((pub.n.bit_length() + 7) // 8, byteorder="big")
    e_bytes = pub.e.to_bytes((pub.e.bit_length() + 7) // 8, byteorder="big")
    kid = f"test-{uuid.uuid4().hex[:8]}"
    pub_jwk = json.dumps(
        {
            "kty": "RSA",
            "kid": kid,
            "alg": "RS256",
            "use": "sig",
            "n": base64.urlsafe_b64encode(n_bytes).rstrip(b"=").decode(),
            "e": base64.urlsafe_b64encode(e_bytes).rstrip(b"=").decode(),
        }
    )
    return private_key, pub_jwk, kid


def _mock_db_with_key(pub_jwk_str: str, kid: str, *, found: bool = True) -> AsyncMock:
    """Create a mock DB that returns a JWK for the given kid.

    Parameters
    ----------
    pub_jwk_str : str
        Public JWK JSON string.
    kid : str
        Key ID.
    found : bool
        Whether the key should be found.

    Returns
    -------
    AsyncMock
        The mock database session.
    """
    db = AsyncMock()
    if found:
        mock_jwk = MagicMock()
        mock_jwk.kid = kid
        mock_jwk.public_key = pub_jwk_str
        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_jwk
    else:
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
    db.execute.return_value = result
    return db


def _sign_token(
    private_key: rsa.RSAPrivateKey,
    kid: str,
    claims: dict[str, object],
) -> str:
    """Create a signed JWT."""
    return pyjwt.encode(
        claims,
        private_key,
        algorithm="RS256",
        headers={"kid": kid},
    )


class TestValidToken:
    """Tests for successful validation."""

    def test_valid_token(self) -> None:
        """Valid token returns valid=True with claims."""

        async def _run() -> None:
            private_key, pub_jwk, kid = _generate_rsa_pair()
            db = _mock_db_with_key(pub_jwk, kid)

            now = datetime.now(timezone.utc)
            token = _sign_token(
                private_key,
                kid,
                {
                    "iss": _ISSUER,
                    "sub": "user-1",
                    "aud": "client-1",
                    "exp": now + timedelta(hours=1),
                    "iat": now,
                    "jti": uuid.uuid4().hex,
                },
            )

            svc = JWTValidationService(_settings(), db)
            result = await svc.validate(token, audience="client-1")
            assert result.valid is True
            assert result.claims is not None
            assert result.claims["sub"] == "user-1"
            assert result.error is None

        asyncio.run(_run())

    def test_valid_without_audience_check(self) -> None:
        """Token without audience check still validates."""

        async def _run() -> None:
            private_key, pub_jwk, kid = _generate_rsa_pair()
            db = _mock_db_with_key(pub_jwk, kid)

            now = datetime.now(timezone.utc)
            token = _sign_token(
                private_key,
                kid,
                {
                    "iss": _ISSUER,
                    "sub": "u",
                    "exp": now + timedelta(hours=1),
                    "iat": now,
                },
            )

            svc = JWTValidationService(_settings(), db)
            result = await svc.validate(token)
            assert result.valid is True

        asyncio.run(_run())

    def test_rotated_key_still_valid(self) -> None:
        """Rotated (non-revoked) key still validates tokens."""

        async def _run() -> None:
            private_key, pub_jwk, kid = _generate_rsa_pair()
            # Rotated key is still non-revoked, so it's found
            db = _mock_db_with_key(pub_jwk, kid)

            now = datetime.now(timezone.utc)
            token = _sign_token(
                private_key,
                kid,
                {
                    "iss": _ISSUER,
                    "sub": "u",
                    "exp": now + timedelta(hours=1),
                    "iat": now,
                },
            )

            svc = JWTValidationService(_settings(), db)
            result = await svc.validate(token)
            assert result.valid is True

        asyncio.run(_run())


class TestExpiredToken:
    """Tests for expired tokens."""

    def test_expired_token(self) -> None:
        """Expired token returns EXPIRED error."""

        async def _run() -> None:
            private_key, pub_jwk, kid = _generate_rsa_pair()
            db = _mock_db_with_key(pub_jwk, kid)

            now = datetime.now(timezone.utc)
            token = _sign_token(
                private_key,
                kid,
                {
                    "iss": _ISSUER,
                    "sub": "u",
                    "exp": now - timedelta(hours=1),
                    "iat": now,
                },
            )

            svc = JWTValidationService(_settings(), db)
            result = await svc.validate(token)
            assert result.valid is False
            assert result.error == TokenError.EXPIRED

        asyncio.run(_run())


class TestInvalidSignature:
    """Tests for signature mismatches."""

    def test_wrong_key_signature(self) -> None:
        """Token signed with wrong key returns INVALID_SIGNATURE."""

        async def _run() -> None:
            _, pub_jwk, kid = _generate_rsa_pair()
            db = _mock_db_with_key(pub_jwk, kid)

            # Sign with a different key
            other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            now = datetime.now(timezone.utc)
            token = _sign_token(
                other_key,
                kid,
                {
                    "iss": _ISSUER,
                    "sub": "u",
                    "exp": now + timedelta(hours=1),
                    "iat": now,
                },
            )

            svc = JWTValidationService(_settings(), db)
            result = await svc.validate(token)
            assert result.valid is False
            assert result.error == TokenError.INVALID_SIGNATURE

        asyncio.run(_run())


class TestKeyNotFound:
    """Tests for missing or revoked keys."""

    def test_unknown_kid(self) -> None:
        """Unknown kid returns KEY_NOT_FOUND."""

        async def _run() -> None:
            private_key, pub_jwk, kid = _generate_rsa_pair()
            # DB returns None for the kid in the token
            db = _mock_db_with_key(pub_jwk, "other-kid", found=False)

            now = datetime.now(timezone.utc)
            token = _sign_token(
                private_key,
                "nonexistent-kid",
                {
                    "iss": _ISSUER,
                    "sub": "u",
                    "exp": now + timedelta(hours=1),
                    "iat": now,
                },
            )

            svc = JWTValidationService(_settings(), db)
            result = await svc.validate(token)
            assert result.valid is False
            assert result.error == TokenError.KEY_NOT_FOUND

        asyncio.run(_run())

    def test_revoked_key_rejected(self) -> None:
        """Revoked key (not found in non-revoked query) returns KEY_NOT_FOUND."""

        async def _run() -> None:
            private_key, pub_jwk, kid = _generate_rsa_pair()
            # Revoked key won't be returned by the query
            db = _mock_db_with_key(pub_jwk, kid, found=False)

            now = datetime.now(timezone.utc)
            token = _sign_token(
                private_key,
                kid,
                {
                    "iss": _ISSUER,
                    "sub": "u",
                    "exp": now + timedelta(hours=1),
                    "iat": now,
                },
            )

            svc = JWTValidationService(_settings(), db)
            result = await svc.validate(token)
            assert result.valid is False
            assert result.error == TokenError.KEY_NOT_FOUND

        asyncio.run(_run())


class TestInvalidClaims:
    """Tests for claims validation."""

    def test_wrong_issuer(self) -> None:
        """Wrong issuer returns INVALID_CLAIMS."""

        async def _run() -> None:
            private_key, pub_jwk, kid = _generate_rsa_pair()
            db = _mock_db_with_key(pub_jwk, kid)

            now = datetime.now(timezone.utc)
            token = _sign_token(
                private_key,
                kid,
                {
                    "iss": "https://evil.com",
                    "sub": "u",
                    "exp": now + timedelta(hours=1),
                    "iat": now,
                },
            )

            svc = JWTValidationService(_settings(), db)
            result = await svc.validate(token)
            assert result.valid is False
            assert result.error == TokenError.INVALID_CLAIMS

        asyncio.run(_run())

    def test_wrong_audience(self) -> None:
        """Wrong audience returns INVALID_CLAIMS."""

        async def _run() -> None:
            private_key, pub_jwk, kid = _generate_rsa_pair()
            db = _mock_db_with_key(pub_jwk, kid)

            now = datetime.now(timezone.utc)
            token = _sign_token(
                private_key,
                kid,
                {
                    "iss": _ISSUER,
                    "sub": "u",
                    "aud": "other-client",
                    "exp": now + timedelta(hours=1),
                    "iat": now,
                },
            )

            svc = JWTValidationService(_settings(), db)
            result = await svc.validate(token, audience="expected-client")
            assert result.valid is False
            assert result.error == TokenError.INVALID_CLAIMS

        asyncio.run(_run())


class TestDecodeError:
    """Tests for malformed tokens."""

    def test_malformed_token(self) -> None:
        """Malformed token returns DECODE_ERROR."""

        async def _run() -> None:
            db = AsyncMock()
            svc = JWTValidationService(_settings(), db)
            result = await svc.validate("not.a.jwt.at.all")
            assert result.valid is False
            assert result.error == TokenError.DECODE_ERROR

        asyncio.run(_run())

    def test_missing_kid_header(self) -> None:
        """Token without kid header returns KEY_NOT_FOUND."""

        async def _run() -> None:
            private_key, _, _ = _generate_rsa_pair()
            db = AsyncMock()

            now = datetime.now(timezone.utc)
            # Sign without kid header
            token = pyjwt.encode(
                {
                    "iss": _ISSUER,
                    "sub": "u",
                    "exp": now + timedelta(hours=1),
                    "iat": now,
                },
                private_key,
                algorithm="RS256",
            )

            svc = JWTValidationService(_settings(), db)
            result = await svc.validate(token)
            assert result.valid is False
            assert result.error == TokenError.KEY_NOT_FOUND

        asyncio.run(_run())


class TestClockSkew:
    """Tests for clock skew tolerance."""

    def test_within_skew_tolerance(self) -> None:
        """Token just expired but within skew is still valid."""

        async def _run() -> None:
            private_key, pub_jwk, kid = _generate_rsa_pair()
            db = _mock_db_with_key(pub_jwk, kid)

            now = datetime.now(timezone.utc)
            # Token expired 3 seconds ago, skew is 5
            token = _sign_token(
                private_key,
                kid,
                {
                    "iss": _ISSUER,
                    "sub": "u",
                    "exp": now - timedelta(seconds=3),
                    "iat": now,
                },
            )

            svc = JWTValidationService(_settings(jwt_clock_skew=5), db)
            result = await svc.validate(token)
            assert result.valid is True

        asyncio.run(_run())

    def test_beyond_skew_tolerance(self) -> None:
        """Token expired beyond skew returns EXPIRED."""

        async def _run() -> None:
            private_key, pub_jwk, kid = _generate_rsa_pair()
            db = _mock_db_with_key(pub_jwk, kid)

            now = datetime.now(timezone.utc)
            # Token expired 10 seconds ago, skew is 5
            token = _sign_token(
                private_key,
                kid,
                {
                    "iss": _ISSUER,
                    "sub": "u",
                    "exp": now - timedelta(seconds=10),
                    "iat": now,
                },
            )

            svc = JWTValidationService(_settings(jwt_clock_skew=5), db)
            result = await svc.validate(token)
            assert result.valid is False
            assert result.error == TokenError.EXPIRED

        asyncio.run(_run())


class TestJWTValidationDecodeErrors:
    """Tests for JWT validation decode error paths."""

    def test_malformed_token(self) -> None:
        """Completely malformed token returns invalid result."""

        async def _run() -> None:
            settings = MagicMock()
            settings.jwt_issuer = "https://test.local"
            svc = JWTValidationService(settings, AsyncMock())
            result = await svc.validate("not.a.valid.jwt")
            assert result.valid is False

        asyncio.run(_run())

    def test_invalid_header(self) -> None:
        """Token with invalid base64 header returns invalid result."""

        async def _run() -> None:
            settings = MagicMock()
            settings.jwt_issuer = "https://test.local"
            svc = JWTValidationService(settings, AsyncMock())
            result = await svc.validate("eyJhbGciOiJSUzI1NiJ9.e30.invalid")
            assert result.valid is False

        asyncio.run(_run())

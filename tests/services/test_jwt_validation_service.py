# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for JWT validation service."""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

import jwt as pyjwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from shomer.core.database import Base
from shomer.core.security import AESEncryption
from shomer.core.settings import Settings
from shomer.models.jwk import JWK, JWKStatus
from shomer.models.password_reset_token import PasswordResetToken  # noqa: F401
from shomer.models.session import Session  # noqa: F401
from shomer.models.user import User  # noqa: F401
from shomer.models.user_email import UserEmail  # noqa: F401
from shomer.models.user_password import UserPassword  # noqa: F401
from shomer.models.user_profile import UserProfile  # noqa: F401
from shomer.models.verification_code import VerificationCode  # noqa: F401
from shomer.services.jwt_validation_service import (
    JWTValidationService,
    TokenError,
)

_ENGINE = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_SESSION_FACTORY = async_sessionmaker(_ENGINE, expire_on_commit=False)
_ISSUER = "https://test.shomer.local"


@pytest.fixture(autouse=True)
def _setup_db() -> Iterator[None]:
    """Create and drop tables for each test."""

    async def _create() -> None:
        async with _ENGINE.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_create())
    yield

    async def _drop() -> None:
        async with _ENGINE.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    asyncio.run(_drop())


def _settings(**overrides: object) -> Settings:
    defaults = {"jwt_issuer": _ISSUER, "jwt_clock_skew": 5}
    defaults.update(overrides)
    return Settings(**defaults)  # type: ignore[arg-type]


def _generate_rsa_pair() -> tuple[rsa.RSAPrivateKey, bytes]:
    """Generate an RSA key pair, return (private_key, public_jwk_json)."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub = private_key.public_key().public_numbers()
    import base64

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
    return private_key, pub_jwk.encode()


async def _insert_key(
    status: JWKStatus = JWKStatus.ACTIVE,
) -> tuple[rsa.RSAPrivateKey, str]:
    """Insert a JWK into the DB and return (private_key, kid)."""
    private_key, pub_jwk_bytes = _generate_rsa_pair()
    pub_jwk = json.loads(pub_jwk_bytes)
    kid = pub_jwk["kid"]

    enc_key = AESEncryption.generate_key()
    enc = AESEncryption(enc_key)
    priv_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )

    async with _SESSION_FACTORY() as session:
        jwk = JWK(
            kid=kid,
            algorithm="RS256",
            public_key=pub_jwk_bytes.decode(),
            private_key_enc=enc.encrypt(priv_pem),
            status=status,
        )
        session.add(jwk)
        await session.commit()

    return private_key, kid


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
        async def _run() -> None:
            private_key, kid = await _insert_key()
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

            async with _SESSION_FACTORY() as session:
                svc = JWTValidationService(_settings(), session)
                result = await svc.validate(token, audience="client-1")
                assert result.valid is True
                assert result.claims is not None
                assert result.claims["sub"] == "user-1"
                assert result.error is None

        asyncio.run(_run())

    def test_valid_without_audience_check(self) -> None:
        async def _run() -> None:
            private_key, kid = await _insert_key()
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

            async with _SESSION_FACTORY() as session:
                svc = JWTValidationService(_settings(), session)
                result = await svc.validate(token)
                assert result.valid is True

        asyncio.run(_run())

    def test_rotated_key_still_valid(self) -> None:
        async def _run() -> None:
            private_key, kid = await _insert_key(status=JWKStatus.ROTATED)
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

            async with _SESSION_FACTORY() as session:
                svc = JWTValidationService(_settings(), session)
                result = await svc.validate(token)
                assert result.valid is True

        asyncio.run(_run())


class TestExpiredToken:
    """Tests for expired tokens."""

    def test_expired_token(self) -> None:
        async def _run() -> None:
            private_key, kid = await _insert_key()
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

            async with _SESSION_FACTORY() as session:
                svc = JWTValidationService(_settings(), session)
                result = await svc.validate(token)
                assert result.valid is False
                assert result.error == TokenError.EXPIRED

        asyncio.run(_run())


class TestInvalidSignature:
    """Tests for signature mismatches."""

    def test_wrong_key_signature(self) -> None:
        async def _run() -> None:
            _, kid = await _insert_key()
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

            async with _SESSION_FACTORY() as session:
                svc = JWTValidationService(_settings(), session)
                result = await svc.validate(token)
                assert result.valid is False
                assert result.error == TokenError.INVALID_SIGNATURE

        asyncio.run(_run())


class TestKeyNotFound:
    """Tests for missing or revoked keys."""

    def test_unknown_kid(self) -> None:
        async def _run() -> None:
            private_key, _ = await _insert_key()
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

            async with _SESSION_FACTORY() as session:
                svc = JWTValidationService(_settings(), session)
                result = await svc.validate(token)
                assert result.valid is False
                assert result.error == TokenError.KEY_NOT_FOUND

        asyncio.run(_run())

    def test_revoked_key_rejected(self) -> None:
        async def _run() -> None:
            private_key, kid = await _insert_key(status=JWKStatus.REVOKED)
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

            async with _SESSION_FACTORY() as session:
                svc = JWTValidationService(_settings(), session)
                result = await svc.validate(token)
                assert result.valid is False
                assert result.error == TokenError.KEY_NOT_FOUND

        asyncio.run(_run())


class TestInvalidClaims:
    """Tests for claims validation."""

    def test_wrong_issuer(self) -> None:
        async def _run() -> None:
            private_key, kid = await _insert_key()
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

            async with _SESSION_FACTORY() as session:
                svc = JWTValidationService(_settings(), session)
                result = await svc.validate(token)
                assert result.valid is False
                assert result.error == TokenError.INVALID_CLAIMS

        asyncio.run(_run())

    def test_wrong_audience(self) -> None:
        async def _run() -> None:
            private_key, kid = await _insert_key()
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

            async with _SESSION_FACTORY() as session:
                svc = JWTValidationService(_settings(), session)
                result = await svc.validate(token, audience="expected-client")
                assert result.valid is False
                assert result.error == TokenError.INVALID_CLAIMS

        asyncio.run(_run())


class TestDecodeError:
    """Tests for malformed tokens."""

    def test_malformed_token(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                svc = JWTValidationService(_settings(), session)
                result = await svc.validate("not.a.jwt.at.all")
                assert result.valid is False
                assert result.error == TokenError.DECODE_ERROR

        asyncio.run(_run())

    def test_missing_kid_header(self) -> None:
        async def _run() -> None:
            private_key, _ = await _insert_key()
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

            async with _SESSION_FACTORY() as session:
                svc = JWTValidationService(_settings(), session)
                result = await svc.validate(token)
                assert result.valid is False
                assert result.error == TokenError.KEY_NOT_FOUND

        asyncio.run(_run())


class TestClockSkew:
    """Tests for clock skew tolerance."""

    def test_within_skew_tolerance(self) -> None:
        async def _run() -> None:
            private_key, kid = await _insert_key()
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

            async with _SESSION_FACTORY() as session:
                svc = JWTValidationService(_settings(jwt_clock_skew=5), session)
                result = await svc.validate(token)
                assert result.valid is True

        asyncio.run(_run())

    def test_beyond_skew_tolerance(self) -> None:
        async def _run() -> None:
            private_key, kid = await _insert_key()
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

            async with _SESSION_FACTORY() as session:
                svc = JWTValidationService(_settings(jwt_clock_skew=5), session)
                result = await svc.validate(token)
                assert result.valid is False
                assert result.error == TokenError.EXPIRED

        asyncio.run(_run())

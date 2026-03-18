# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for JWT creation service."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Iterator

import jwt
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from shomer.core.database import Base
from shomer.core.security import AESEncryption
from shomer.core.settings import Settings
from shomer.models.jwk import JWK  # noqa: F401
from shomer.models.password_reset_token import PasswordResetToken  # noqa: F401
from shomer.models.session import Session  # noqa: F401
from shomer.models.user import User  # noqa: F401
from shomer.models.user_email import UserEmail  # noqa: F401
from shomer.models.user_password import UserPassword  # noqa: F401
from shomer.models.user_profile import UserProfile  # noqa: F401
from shomer.models.verification_code import VerificationCode  # noqa: F401
from shomer.services.jwk_service import JWKService
from shomer.services.jwt_service import JWTService

_ENGINE = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_SESSION_FACTORY = async_sessionmaker(_ENGINE, expire_on_commit=False)


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


def _make_settings(**overrides: object) -> Settings:
    defaults = {
        "jwt_issuer": "https://test.shomer.local",
        "jwt_access_token_exp": 3600,
        "jwt_id_token_exp": 1800,
        "rsa_key_size": 2048,
    }
    defaults.update(overrides)
    return Settings(**defaults)  # type: ignore[arg-type]


class TestCreateAccessToken:
    """Tests for JWTService.create_access_token()."""

    def test_creates_signed_jwt(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                key = AESEncryption.generate_key()
                enc = AESEncryption(key)
                settings = _make_settings()

                # Generate a signing key first
                jwk_svc = JWKService(session, enc, key_size=2048)
                active_key = await jwk_svc.generate_key()

                svc = JWTService(settings, session, enc)
                token = await svc.create_access_token(sub="user-123", aud="client-abc")

                # Decode with public key
                pub_jwk = json.loads(active_key.public_key)
                pub_key = jwt.algorithms.RSAAlgorithm.from_jwk(pub_jwk)
                decoded = jwt.decode(
                    token,
                    pub_key,  # type: ignore[arg-type]
                    algorithms=["RS256"],
                    audience="client-abc",
                    issuer="https://test.shomer.local",
                )
                assert decoded["sub"] == "user-123"
                assert decoded["aud"] == "client-abc"
                assert decoded["iss"] == "https://test.shomer.local"

        asyncio.run(_run())

    def test_includes_standard_claims(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                key = AESEncryption.generate_key()
                enc = AESEncryption(key)
                settings = _make_settings()

                jwk_svc = JWKService(session, enc, key_size=2048)
                active_key = await jwk_svc.generate_key()

                svc = JWTService(settings, session, enc)
                token = await svc.create_access_token(sub="u1", aud="c1")

                pub_jwk = json.loads(active_key.public_key)
                pub_key = jwt.algorithms.RSAAlgorithm.from_jwk(pub_jwk)
                decoded = jwt.decode(
                    token,
                    pub_key,  # type: ignore[arg-type]
                    algorithms=["RS256"],
                    audience="c1",
                )
                assert "iat" in decoded
                assert "exp" in decoded
                assert "jti" in decoded

        asyncio.run(_run())

    def test_embeds_scopes(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                key = AESEncryption.generate_key()
                enc = AESEncryption(key)
                settings = _make_settings()

                jwk_svc = JWKService(session, enc, key_size=2048)
                active_key = await jwk_svc.generate_key()

                svc = JWTService(settings, session, enc)
                token = await svc.create_access_token(
                    sub="u1", aud="c1", scopes=["openid", "profile"]
                )

                pub_jwk = json.loads(active_key.public_key)
                pub_key = jwt.algorithms.RSAAlgorithm.from_jwk(pub_jwk)
                decoded = jwt.decode(
                    token,
                    pub_key,  # type: ignore[arg-type]
                    algorithms=["RS256"],
                    audience="c1",
                )
                assert decoded["scope"] == "openid profile"

        asyncio.run(_run())

    def test_kid_header(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                key = AESEncryption.generate_key()
                enc = AESEncryption(key)
                settings = _make_settings()

                jwk_svc = JWKService(session, enc, key_size=2048)
                active_key = await jwk_svc.generate_key()

                svc = JWTService(settings, session, enc)
                token = await svc.create_access_token(sub="u1", aud="c1")

                header = jwt.get_unverified_header(token)
                assert header["kid"] == active_key.kid
                assert header["alg"] == "RS256"

        asyncio.run(_run())

    def test_raises_without_active_key(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                key = AESEncryption.generate_key()
                enc = AESEncryption(key)
                settings = _make_settings()

                svc = JWTService(settings, session, enc)
                with pytest.raises(RuntimeError, match="No active signing key"):
                    await svc.create_access_token(sub="u1", aud="c1")

        asyncio.run(_run())


class TestCreateIdToken:
    """Tests for JWTService.create_id_token()."""

    def test_creates_id_token_with_nonce(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                key = AESEncryption.generate_key()
                enc = AESEncryption(key)
                settings = _make_settings()

                jwk_svc = JWKService(session, enc, key_size=2048)
                active_key = await jwk_svc.generate_key()

                svc = JWTService(settings, session, enc)
                token = await svc.create_id_token(sub="u1", aud="c1", nonce="abc123")

                pub_jwk = json.loads(active_key.public_key)
                pub_key = jwt.algorithms.RSAAlgorithm.from_jwk(pub_jwk)
                decoded = jwt.decode(
                    token,
                    pub_key,  # type: ignore[arg-type]
                    algorithms=["RS256"],
                    audience="c1",
                )
                assert decoded["nonce"] == "abc123"

        asyncio.run(_run())

    def test_id_token_uses_configured_exp(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                key = AESEncryption.generate_key()
                enc = AESEncryption(key)
                settings = _make_settings(jwt_id_token_exp=600)

                jwk_svc = JWKService(session, enc, key_size=2048)
                active_key = await jwk_svc.generate_key()

                svc = JWTService(settings, session, enc)
                token = await svc.create_id_token(sub="u1", aud="c1")

                pub_jwk = json.loads(active_key.public_key)
                pub_key = jwt.algorithms.RSAAlgorithm.from_jwk(pub_jwk)
                decoded = jwt.decode(
                    token,
                    pub_key,  # type: ignore[arg-type]
                    algorithms=["RS256"],
                    audience="c1",
                )
                # exp - iat should be ~600
                diff = decoded["exp"] - decoded["iat"]
                assert diff == 600

        asyncio.run(_run())

    def test_extra_claims(self) -> None:
        async def _run() -> None:
            async with _SESSION_FACTORY() as session:
                key = AESEncryption.generate_key()
                enc = AESEncryption(key)
                settings = _make_settings()

                jwk_svc = JWKService(session, enc, key_size=2048)
                active_key = await jwk_svc.generate_key()

                svc = JWTService(settings, session, enc)
                token = await svc.create_id_token(
                    sub="u1",
                    aud="c1",
                    extra_claims={"email": "user@example.com", "name": "Test"},
                )

                pub_jwk = json.loads(active_key.public_key)
                pub_key = jwt.algorithms.RSAAlgorithm.from_jwk(pub_jwk)
                decoded = jwt.decode(
                    token,
                    pub_key,  # type: ignore[arg-type]
                    algorithms=["RS256"],
                    audience="c1",
                )
                assert decoded["email"] == "user@example.com"
                assert decoded["name"] == "Test"

        asyncio.run(_run())

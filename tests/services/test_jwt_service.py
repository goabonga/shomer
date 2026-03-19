# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for JWT creation service."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import jwt
import pytest

from shomer.core.security import AESEncryption
from shomer.services.jwt_service import JWTService


def _make_settings(**overrides: object) -> MagicMock:
    """Create a mock Settings object with sensible defaults."""
    settings = MagicMock()
    settings.jwt_issuer = overrides.get("jwt_issuer", "https://test.shomer.local")
    settings.jwt_access_token_exp = overrides.get("jwt_access_token_exp", 3600)
    settings.jwt_id_token_exp = overrides.get("jwt_id_token_exp", 1800)
    settings.rsa_key_size = overrides.get("rsa_key_size", 2048)
    return settings


def _make_jwk_and_service(
    settings: MagicMock | None = None,
) -> tuple[JWTService, MagicMock, bytes]:
    """Create a JWTService with a real RSA key for signing.

    Returns
    -------
    tuple[JWTService, MagicMock, bytes]
        The service, mock active key, and public JWK bytes for verification.
    """
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    if settings is None:
        settings = _make_settings()

    key = AESEncryption.generate_key()
    enc = AESEncryption(key)

    # Generate real RSA key
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    private_key_enc = enc.encrypt(private_pem)

    # Build public JWK JSON
    import base64

    pub = private_key.public_key().public_numbers()
    n_bytes = pub.n.to_bytes((pub.n.bit_length() + 7) // 8, byteorder="big")
    e_bytes = pub.e.to_bytes((pub.e.bit_length() + 7) // 8, byteorder="big")
    pub_jwk = json.dumps(
        {
            "kty": "RSA",
            "kid": "test-kid-001",
            "alg": "RS256",
            "use": "sig",
            "n": base64.urlsafe_b64encode(n_bytes).rstrip(b"=").decode(),
            "e": base64.urlsafe_b64encode(e_bytes).rstrip(b"=").decode(),
        }
    )

    mock_active_key = MagicMock()
    mock_active_key.kid = "test-kid-001"
    mock_active_key.algorithm = "RS256"
    mock_active_key.private_key_enc = private_key_enc
    mock_active_key.public_key = pub_jwk

    db = AsyncMock()
    svc = JWTService(settings, db, enc)

    # Patch the JWK service to return our mock key
    svc.jwk_service = MagicMock()
    svc.jwk_service.get_active_signing_key = AsyncMock(return_value=mock_active_key)

    return svc, mock_active_key, pub_jwk.encode()


class TestCreateAccessToken:
    """Tests for JWTService.create_access_token()."""

    def test_creates_signed_jwt(self) -> None:
        """Creates a JWT that can be decoded with the public key."""

        async def _run() -> None:
            svc, active_key, pub_jwk_bytes = _make_jwk_and_service()
            token = await svc.create_access_token(sub="user-123", aud="client-abc")

            pub_jwk = json.loads(pub_jwk_bytes)
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
        """JWT includes iat, exp, and jti claims."""

        async def _run() -> None:
            svc, active_key, pub_jwk_bytes = _make_jwk_and_service()
            token = await svc.create_access_token(sub="u1", aud="c1")

            pub_jwk = json.loads(pub_jwk_bytes)
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
        """JWT includes scope claim as space-separated string."""

        async def _run() -> None:
            svc, active_key, pub_jwk_bytes = _make_jwk_and_service()
            token = await svc.create_access_token(
                sub="u1", aud="c1", scopes=["openid", "profile"]
            )

            pub_jwk = json.loads(pub_jwk_bytes)
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
        """JWT header contains the correct kid."""

        async def _run() -> None:
            svc, active_key, _ = _make_jwk_and_service()
            token = await svc.create_access_token(sub="u1", aud="c1")

            header = jwt.get_unverified_header(token)
            assert header["kid"] == active_key.kid
            assert header["alg"] == "RS256"

        asyncio.run(_run())

    def test_raises_without_active_key(self) -> None:
        """Raises RuntimeError when no active signing key exists."""

        async def _run() -> None:
            settings = _make_settings()
            db = AsyncMock()
            enc = MagicMock()
            svc = JWTService(settings, db, enc)
            svc.jwk_service = MagicMock()
            svc.jwk_service.get_active_signing_key = AsyncMock(return_value=None)

            with pytest.raises(RuntimeError, match="No active signing key"):
                await svc.create_access_token(sub="u1", aud="c1")

        asyncio.run(_run())


class TestCreateIdToken:
    """Tests for JWTService.create_id_token()."""

    def test_creates_id_token_with_nonce(self) -> None:
        """ID token includes nonce claim."""

        async def _run() -> None:
            svc, active_key, pub_jwk_bytes = _make_jwk_and_service()
            token = await svc.create_id_token(sub="u1", aud="c1", nonce="abc123")

            pub_jwk = json.loads(pub_jwk_bytes)
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
        """ID token uses jwt_id_token_exp setting."""

        async def _run() -> None:
            settings = _make_settings(jwt_id_token_exp=600)
            svc, active_key, pub_jwk_bytes = _make_jwk_and_service(settings=settings)
            token = await svc.create_id_token(sub="u1", aud="c1")

            pub_jwk = json.loads(pub_jwk_bytes)
            pub_key = jwt.algorithms.RSAAlgorithm.from_jwk(pub_jwk)
            decoded = jwt.decode(
                token,
                pub_key,  # type: ignore[arg-type]
                algorithms=["RS256"],
                audience="c1",
            )
            diff = decoded["exp"] - decoded["iat"]
            assert diff == 600

        asyncio.run(_run())

    def test_extra_claims(self) -> None:
        """ID token includes extra claims."""

        async def _run() -> None:
            svc, active_key, pub_jwk_bytes = _make_jwk_and_service()
            token = await svc.create_id_token(
                sub="u1",
                aud="c1",
                extra_claims={"email": "user@example.com", "name": "Test"},
            )

            pub_jwk = json.loads(pub_jwk_bytes)
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


class TestJWTServiceExtraClaims:
    """Test JWTService.create_access_token with extra_claims."""

    def test_create_access_token_with_extra_claims(self) -> None:
        """create_access_token includes scope and extra claims."""
        from unittest.mock import patch as _patch

        from shomer.services.jwt_service import JWTService

        async def _run() -> None:
            mock_settings = MagicMock()
            mock_settings.jwt_issuer = "https://test.local"
            mock_settings.jwt_access_token_exp = 3600
            mock_db = AsyncMock()
            mock_enc = MagicMock()

            svc = JWTService(mock_settings, mock_db, mock_enc)
            with _patch.object(svc, "_sign", new_callable=AsyncMock) as mock_sign:
                mock_sign.return_value = "signed-jwt"
                result = await svc.create_access_token(
                    sub="user-1",
                    aud="client-1",
                    scopes=["openid", "profile"],
                    extra_claims={"email": "test@example.com"},
                )
                assert result == "signed-jwt"
                call_kwargs = mock_sign.call_args
                extra = call_kwargs[1].get("extra_claims", {})
                assert extra.get("scope") == "openid profile"
                assert extra.get("email") == "test@example.com"

        asyncio.run(_run())

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for JWK model."""

import json

from shomer.core.security import AESEncryption
from shomer.models.jwk import JWK, JWKStatus


class TestJWKStatus:
    """Tests for JWKStatus enum."""

    def test_active_value(self) -> None:
        assert JWKStatus.ACTIVE.value == "active"

    def test_rotated_value(self) -> None:
        assert JWKStatus.ROTATED.value == "rotated"

    def test_revoked_value(self) -> None:
        assert JWKStatus.REVOKED.value == "revoked"

    def test_is_str_enum(self) -> None:
        assert isinstance(JWKStatus.ACTIVE, str)


class TestJWKModel:
    """Tests for JWK SQLAlchemy model definition."""

    def test_tablename(self) -> None:
        assert JWK.__tablename__ == "jwks"

    def test_required_fields(self) -> None:
        enc = AESEncryption(AESEncryption.generate_key())
        priv_enc = enc.encrypt(b"private-key-material")
        pub_json = json.dumps({"kty": "RSA", "n": "...", "e": "AQAB"})

        jwk = JWK(
            kid="key-2026-01",
            algorithm="RS256",
            public_key=pub_json,
            private_key_enc=priv_enc,
        )
        assert jwk.kid == "key-2026-01"
        assert jwk.algorithm == "RS256"
        assert jwk.public_key == pub_json
        assert jwk.private_key_enc == priv_enc

    def test_encrypted_private_key_roundtrip(self) -> None:
        key = AESEncryption.generate_key()
        enc = AESEncryption(key)
        plaintext = b"super-secret-rsa-key"
        ciphertext = enc.encrypt(plaintext)

        jwk = JWK(
            kid="rt-1",
            algorithm="RS256",
            public_key="{}",
            private_key_enc=ciphertext,
        )

        dec = AESEncryption(key)
        assert dec.decrypt(jwk.private_key_enc) == plaintext

    def test_status_default(self) -> None:
        col = JWK.__table__.c.status
        assert col.default.arg is JWKStatus.ACTIVE

    def test_kid_column_unique(self) -> None:
        col = JWK.__table__.c.kid
        assert col.unique is True

    def test_kid_column_indexed(self) -> None:
        col = JWK.__table__.c.kid
        assert col.index is True

    def test_kid_column_not_nullable(self) -> None:
        col = JWK.__table__.c.kid
        assert col.nullable is False

    def test_status_column_indexed(self) -> None:
        col = JWK.__table__.c.status
        assert col.index is True

    def test_status_column_not_nullable(self) -> None:
        col = JWK.__table__.c.status
        assert col.nullable is False

    def test_public_key_not_nullable(self) -> None:
        col = JWK.__table__.c.public_key
        assert col.nullable is False

    def test_private_key_enc_not_nullable(self) -> None:
        col = JWK.__table__.c.private_key_enc
        assert col.nullable is False

    def test_algorithm_not_nullable(self) -> None:
        col = JWK.__table__.c.algorithm
        assert col.nullable is False

    def test_repr(self) -> None:
        jwk = JWK(
            kid="test-kid",
            algorithm="RS256",
            public_key="{}",
            private_key_enc=b"enc",
            status=JWKStatus.ROTATED,
        )
        r = repr(jwk)
        assert "kid=test-kid" in r
        assert "alg=RS256" in r
        assert "status=rotated" in r

    def test_all_statuses_assignable(self) -> None:
        for status in JWKStatus:
            jwk = JWK(
                kid=f"k-{status.value}",
                algorithm="RS256",
                public_key="{}",
                private_key_enc=b"x",
                status=status,
            )
            assert jwk.status == status

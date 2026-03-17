# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for shomer.core.security."""

import pytest
from cryptography.exceptions import InvalidTag

from shomer.core.security import (
    AESEncryption,
    Argon2Params,
    check_needs_rehash,
    constant_time_compare,
    hash_password,
    make_hasher,
    verify_password,
)

# ---- Argon2id ---------------------------------------------------------


class TestHashPassword:
    def test_hash_returns_argon2id_string(self) -> None:
        h = hash_password("secret")
        assert h.startswith("$argon2id$")

    def test_hash_is_different_each_time(self) -> None:
        assert hash_password("secret") != hash_password("secret")

    def test_hash_with_custom_hasher(self) -> None:
        hasher = make_hasher(Argon2Params(time_cost=1, memory_cost=16384))
        h = hash_password("secret", hasher=hasher)
        assert h.startswith("$argon2id$")


class TestVerifyPassword:
    def test_correct_password(self) -> None:
        h = hash_password("secret")
        assert verify_password("secret", h) is True

    def test_wrong_password(self) -> None:
        h = hash_password("secret")
        assert verify_password("wrong", h) is False

    def test_verify_with_custom_hasher(self) -> None:
        hasher = make_hasher(Argon2Params(time_cost=1, memory_cost=16384))
        h = hash_password("secret", hasher=hasher)
        assert verify_password("secret", h, hasher=hasher) is True

    def test_empty_password(self) -> None:
        h = hash_password("")
        assert verify_password("", h) is True
        assert verify_password("x", h) is False


class TestCheckNeedsRehash:
    def test_current_params_no_rehash(self) -> None:
        h = hash_password("secret")
        assert check_needs_rehash(h) is False

    def test_different_params_needs_rehash(self) -> None:
        weak = make_hasher(Argon2Params(time_cost=1, memory_cost=16384))
        h = hash_password("secret", hasher=weak)
        assert check_needs_rehash(h) is True


# ---- AES-256-GCM ------------------------------------------------------


class TestAESEncryption:
    def test_encrypt_decrypt_roundtrip(self) -> None:
        enc = AESEncryption(AESEncryption.generate_key())
        plaintext = b"hello world"
        assert enc.decrypt(enc.encrypt(plaintext)) == plaintext

    def test_encrypt_produces_different_ciphertext(self) -> None:
        enc = AESEncryption(AESEncryption.generate_key())
        ct1 = enc.encrypt(b"same")
        ct2 = enc.encrypt(b"same")
        assert ct1 != ct2  # different nonces

    def test_from_base64(self) -> None:
        key_b64 = AESEncryption.generate_key_b64()
        enc = AESEncryption.from_base64(key_b64)
        assert enc.decrypt(enc.encrypt(b"test")) == b"test"

    def test_wrong_key_fails(self) -> None:
        enc1 = AESEncryption(AESEncryption.generate_key())
        enc2 = AESEncryption(AESEncryption.generate_key())
        ct = enc1.encrypt(b"secret")
        with pytest.raises(InvalidTag):
            enc2.decrypt(ct)

    def test_tampered_ciphertext_fails(self) -> None:
        enc = AESEncryption(AESEncryption.generate_key())
        ct = bytearray(enc.encrypt(b"secret"))
        ct[-1] ^= 0xFF  # flip last byte
        with pytest.raises(InvalidTag):
            enc.decrypt(bytes(ct))

    def test_invalid_key_size(self) -> None:
        with pytest.raises(ValueError, match="32 bytes"):
            AESEncryption(b"short")

    def test_generate_key_length(self) -> None:
        assert len(AESEncryption.generate_key()) == 32

    def test_empty_plaintext(self) -> None:
        enc = AESEncryption(AESEncryption.generate_key())
        assert enc.decrypt(enc.encrypt(b"")) == b""


# ---- Constant-time comparison ------------------------------------------


class TestConstantTimeCompare:
    def test_equal_strings(self) -> None:
        assert constant_time_compare("abc", "abc") is True

    def test_unequal_strings(self) -> None:
        assert constant_time_compare("abc", "xyz") is False

    def test_equal_bytes(self) -> None:
        assert constant_time_compare(b"abc", b"abc") is True

    def test_unequal_bytes(self) -> None:
        assert constant_time_compare(b"abc", b"xyz") is False

    def test_empty_values(self) -> None:
        assert constant_time_compare("", "") is True
        assert constant_time_compare(b"", b"") is True

    def test_different_lengths(self) -> None:
        assert constant_time_compare("short", "longer") is False

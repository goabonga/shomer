# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Security utilities for password hashing and symmetric encryption."""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


@dataclass(frozen=True)
class Argon2Params:
    """Argon2id tunable parameters."""

    time_cost: int = 3
    memory_cost: int = 65536  # 64 MiB
    parallelism: int = 4
    hash_len: int = 32
    salt_len: int = 16


_default_params = Argon2Params()

_password_hasher = PasswordHasher(
    time_cost=_default_params.time_cost,
    memory_cost=_default_params.memory_cost,
    parallelism=_default_params.parallelism,
    hash_len=_default_params.hash_len,
    salt_len=_default_params.salt_len,
)


def make_hasher(params: Argon2Params | None = None) -> PasswordHasher:
    """Create a PasswordHasher with the given parameters."""
    p = params or _default_params
    return PasswordHasher(
        time_cost=p.time_cost,
        memory_cost=p.memory_cost,
        parallelism=p.parallelism,
        hash_len=p.hash_len,
        salt_len=p.salt_len,
    )


def hash_password(password: str, *, hasher: PasswordHasher | None = None) -> str:
    """Hash a password using Argon2id."""
    h = hasher or _password_hasher
    return h.hash(password)


def verify_password(
    password: str, password_hash: str, *, hasher: PasswordHasher | None = None
) -> bool:
    """Verify a password against its Argon2id hash."""
    h = hasher or _password_hasher
    try:
        h.verify(password_hash, password)
        return True
    except VerifyMismatchError:
        return False


def check_needs_rehash(
    password_hash: str, *, hasher: PasswordHasher | None = None
) -> bool:
    """Check if a hash needs to be re-hashed with current parameters."""
    h = hasher or _password_hasher
    return h.check_needs_rehash(password_hash)


# ---------------------------------------------------------------------------
# AES-256-GCM symmetric encryption
# ---------------------------------------------------------------------------


class AESEncryption:
    """AES-256-GCM authenticated encryption.

    Ciphertext layout: ``nonce (12 bytes) || ciphertext+tag``.
    """

    NONCE_SIZE = 12  # 96 bits, recommended for GCM
    KEY_SIZE = 32  # 256 bits

    def __init__(self, key: bytes) -> None:
        if len(key) != self.KEY_SIZE:
            raise ValueError(f"Key must be {self.KEY_SIZE} bytes, got {len(key)}")
        self._aesgcm = AESGCM(key)

    @classmethod
    def from_base64(cls, key_b64: str) -> AESEncryption:
        """Create an instance from a base64-encoded key."""
        return cls(base64.b64decode(key_b64))

    @staticmethod
    def generate_key() -> bytes:
        """Generate a random 256-bit key."""
        return os.urandom(AESEncryption.KEY_SIZE)

    @staticmethod
    def generate_key_b64() -> str:
        """Generate a random 256-bit key as a base64 string."""
        return base64.b64encode(AESEncryption.generate_key()).decode("ascii")

    def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt *plaintext* and return ``nonce || ciphertext``."""
        nonce = os.urandom(self.NONCE_SIZE)
        ciphertext = self._aesgcm.encrypt(nonce, plaintext, None)
        return nonce + ciphertext

    def decrypt(self, data: bytes) -> bytes:
        """Decrypt ``nonce || ciphertext`` and return plaintext."""
        nonce = data[: self.NONCE_SIZE]
        ciphertext = data[self.NONCE_SIZE :]
        return self._aesgcm.decrypt(nonce, ciphertext, None)

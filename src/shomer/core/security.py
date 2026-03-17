# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Security utilities for password hashing and symmetric encryption."""

from __future__ import annotations

from dataclasses import dataclass

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


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

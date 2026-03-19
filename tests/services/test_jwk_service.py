# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for RSA key management service."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

from shomer.core.security import AESEncryption
from shomer.models.jwk import JWKStatus
from shomer.services.jwk_service import JWKService


def _make_service(*, key_size: int = 2048) -> tuple[JWKService, AsyncMock]:
    """Create a JWKService with mocked DB and real AES encryption.

    Returns
    -------
    tuple[JWKService, AsyncMock]
        The service and the mock database session.
    """
    key = AESEncryption.generate_key()
    enc = AESEncryption(key)
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.execute = AsyncMock()
    return JWKService(db, enc, key_size=key_size), db


class TestGenerateKey:
    """Tests for JWKService.generate_key()."""

    def test_creates_active_key(self) -> None:
        """Generated key has ACTIVE status and shomer- prefix kid."""

        async def _run() -> None:
            svc, db = _make_service()
            # _rotate_active_keys executes an UPDATE; mock it
            db.execute.return_value = MagicMock()

            jwk = await svc.generate_key()
            assert jwk.status == JWKStatus.ACTIVE
            assert jwk.kid.startswith("shomer-")
            assert jwk.algorithm == "RS256"

        asyncio.run(_run())

    def test_public_key_is_valid_jwk_json(self) -> None:
        """Public key is valid JWK JSON with RSA components."""

        async def _run() -> None:
            svc, db = _make_service()
            db.execute.return_value = MagicMock()

            jwk = await svc.generate_key()
            pub = json.loads(jwk.public_key)
            assert pub["kty"] == "RSA"
            assert pub["use"] == "sig"
            assert "n" in pub
            assert "e" in pub

        asyncio.run(_run())

    def test_private_key_is_encrypted(self) -> None:
        """Private key can be decrypted to PEM format."""

        async def _run() -> None:
            key = AESEncryption.generate_key()
            enc = AESEncryption(key)
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()
            db.execute = AsyncMock()
            db.execute.return_value = MagicMock()

            svc = JWKService(db, enc)
            jwk = await svc.generate_key()
            # Decrypting with same key should yield PEM
            dec = AESEncryption(key)
            plaintext = dec.decrypt(jwk.private_key_enc)
            assert b"BEGIN PRIVATE KEY" in plaintext

        asyncio.run(_run())

    def test_rotates_existing_active_key(self) -> None:
        """Generating a new key calls _rotate_active_keys."""

        async def _run() -> None:
            svc, db = _make_service()
            db.execute.return_value = MagicMock()

            # Generate first key
            first = await svc.generate_key()
            first_kid = first.kid

            # Generate second key (should call rotate)
            second = await svc.generate_key()
            assert second.kid != first_kid
            assert second.status == JWKStatus.ACTIVE
            # _rotate_active_keys was called (execute was called for UPDATE)
            assert db.execute.call_count >= 2

        asyncio.run(_run())


class TestRotate:
    """Tests for JWKService.rotate()."""

    def test_rotate_returns_new_active(self) -> None:
        """Rotate returns a new active key."""

        async def _run() -> None:
            svc, db = _make_service()
            db.execute.return_value = MagicMock()

            new_key = await svc.rotate()
            assert new_key.status == JWKStatus.ACTIVE

        asyncio.run(_run())


class TestRevoke:
    """Tests for JWKService.revoke()."""

    def test_revoke_existing_key(self) -> None:
        """Revoking an existing key sets its status to REVOKED."""

        async def _run() -> None:
            svc, db = _make_service()

            mock_jwk = MagicMock()
            mock_jwk.kid = "test-kid"
            mock_jwk.status = JWKStatus.ACTIVE

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_jwk
            db.execute.return_value = result

            revoked = await svc.revoke("test-kid")
            assert revoked is not None
            assert revoked.status == JWKStatus.REVOKED

        asyncio.run(_run())

    def test_revoke_nonexistent_returns_none(self) -> None:
        """Revoking a nonexistent kid returns None."""

        async def _run() -> None:
            svc, db = _make_service()

            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db.execute.return_value = result

            revoked = await svc.revoke("nonexistent-kid")
            assert revoked is None

        asyncio.run(_run())


class TestGetActiveSigningKey:
    """Tests for JWKService.get_active_signing_key()."""

    def test_returns_none_when_no_keys(self) -> None:
        """Returns None when no active key exists."""

        async def _run() -> None:
            svc, db = _make_service()

            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db.execute.return_value = result

            active = await svc.get_active_signing_key()
            assert active is None

        asyncio.run(_run())

    def test_returns_active_key(self) -> None:
        """Returns the active key when one exists."""

        async def _run() -> None:
            svc, db = _make_service()

            mock_jwk = MagicMock()
            mock_jwk.kid = "active-kid"
            mock_jwk.status = JWKStatus.ACTIVE

            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_jwk
            db.execute.return_value = result

            active = await svc.get_active_signing_key()
            assert active is not None
            assert active.kid == "active-kid"

        asyncio.run(_run())


class TestGetPublicKeys:
    """Tests for JWKService.get_public_keys()."""

    def test_returns_active_and_rotated(self) -> None:
        """Returns all non-revoked keys."""

        async def _run() -> None:
            svc, db = _make_service()

            mock_key1 = MagicMock()
            mock_key2 = MagicMock()

            result = MagicMock()
            scalars_mock = MagicMock()
            scalars_mock.all.return_value = [mock_key1, mock_key2]
            result.scalars.return_value = scalars_mock
            db.execute.return_value = result

            keys = await svc.get_public_keys()
            assert len(keys) == 2

        asyncio.run(_run())

    def test_excludes_revoked(self) -> None:
        """Returns empty when all keys are revoked."""

        async def _run() -> None:
            svc, db = _make_service()

            result = MagicMock()
            scalars_mock = MagicMock()
            scalars_mock.all.return_value = []
            result.scalars.return_value = scalars_mock
            db.execute.return_value = result

            keys = await svc.get_public_keys()
            assert len(keys) == 0

        asyncio.run(_run())

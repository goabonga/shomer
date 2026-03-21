# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""MFA service: TOTP, backup codes, and email fallback.

Implements RFC 6238 TOTP, single-use backup codes with Argon2id
hashing, and email-based 6-digit verification codes.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shomer.core.security import AESEncryption, hash_password, verify_password
from shomer.core.settings import Settings
from shomer.models.mfa_backup_code import MFABackupCode
from shomer.models.mfa_email_code import MFAEmailCode

#: Number of backup codes to generate.
BACKUP_CODE_COUNT = 10

#: Length of each backup code (characters).
BACKUP_CODE_LENGTH = 8

#: Email code TTL in seconds (5 minutes).
EMAIL_CODE_TTL = timedelta(minutes=5)

#: TOTP time step in seconds (RFC 6238 default).
TOTP_PERIOD = 30

#: Number of digits in a TOTP code.
TOTP_DIGITS = 6


class MFAError(Exception):
    """Raised when an MFA operation fails.

    Attributes
    ----------
    message : str
        Human-readable error description.
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class MFAService:
    """Unified MFA service supporting TOTP, backup codes, and email fallback.

    Attributes
    ----------
    session : AsyncSession
        Database session.
    settings : Settings
        Application configuration.
    """

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    # ── TOTP ──────────────────────────────────────────────────────────

    @staticmethod
    def generate_totp_secret() -> str:
        """Generate a random TOTP secret (base32 encoded, 20 bytes).

        Returns
        -------
        str
            Base32-encoded secret suitable for QR provisioning.
        """
        return base64.b32encode(secrets.token_bytes(20)).decode("ascii")

    @staticmethod
    def get_provisioning_uri(
        secret: str,
        *,
        email: str,
        issuer: str = "Shomer",
    ) -> str:
        """Build an ``otpauth://`` provisioning URI for QR code generation.

        Parameters
        ----------
        secret : str
            Base32-encoded TOTP secret.
        email : str
            User's email (the account label).
        issuer : str
            Issuer name displayed in authenticator apps.

        Returns
        -------
        str
            An ``otpauth://totp/...`` URI.
        """
        label = quote(f"{issuer}:{email}", safe="")
        params = (
            f"secret={secret}&issuer={quote(issuer, safe='')}"
            f"&algorithm=SHA1&digits={TOTP_DIGITS}&period={TOTP_PERIOD}"
        )
        return f"otpauth://totp/{label}?{params}"

    @staticmethod
    def generate_totp_code(secret: str, *, time_offset: int = 0) -> str:
        """Generate a TOTP code for the current time step.

        Implements RFC 6238 / RFC 4226 HOTP with SHA-1.

        Parameters
        ----------
        secret : str
            Base32-encoded TOTP secret.
        time_offset : int
            Number of time steps to offset (for tolerance window).

        Returns
        -------
        str
            Zero-padded 6-digit TOTP code.
        """
        key = base64.b32decode(secret, casefold=True)
        counter = int(time.time()) // TOTP_PERIOD + time_offset
        counter_bytes = struct.pack(">Q", counter)
        mac = hmac.new(key, counter_bytes, hashlib.sha1).digest()
        offset = mac[-1] & 0x0F
        truncated = struct.unpack(">I", mac[offset : offset + 4])[0] & 0x7FFFFFFF
        code = truncated % (10**TOTP_DIGITS)
        return str(code).zfill(TOTP_DIGITS)

    @staticmethod
    def verify_totp_code(secret: str, code: str) -> bool:
        """Verify a TOTP code with ±1 period tolerance.

        Parameters
        ----------
        secret : str
            Base32-encoded TOTP secret.
        code : str
            The 6-digit code to verify.

        Returns
        -------
        bool
            ``True`` if the code matches any of the three time windows.
        """
        for offset in (-1, 0, 1):
            expected = MFAService.generate_totp_code(secret, time_offset=offset)
            if hmac.compare_digest(code, expected):
                return True
        return False

    def encrypt_totp_secret(self, secret: str) -> str:
        """Encrypt a TOTP secret with AES-256-GCM.

        Parameters
        ----------
        secret : str
            Base32-encoded TOTP secret (plaintext).

        Returns
        -------
        str
            Base64-encoded encrypted secret.
        """
        enc = AESEncryption.from_base64(self.settings.jwk_encryption_key)
        encrypted = enc.encrypt(secret.encode("utf-8"))
        return base64.b64encode(encrypted).decode("ascii")

    def decrypt_totp_secret(self, encrypted: str) -> str:
        """Decrypt an AES-256-GCM encrypted TOTP secret.

        Parameters
        ----------
        encrypted : str
            Base64-encoded encrypted secret.

        Returns
        -------
        str
            Base32-encoded TOTP secret (plaintext).
        """
        enc = AESEncryption.from_base64(self.settings.jwk_encryption_key)
        data = base64.b64decode(encrypted)
        return enc.decrypt(data).decode("utf-8")

    # ── Backup codes ──────────────────────────────────────────────────

    @staticmethod
    def generate_backup_codes(count: int = BACKUP_CODE_COUNT) -> list[str]:
        """Generate a set of single-use backup codes.

        Parameters
        ----------
        count : int
            Number of codes to generate.

        Returns
        -------
        list[str]
            Raw backup codes (to show to the user once).
        """
        return [
            secrets.token_hex(BACKUP_CODE_LENGTH // 2).upper() for _ in range(count)
        ]

    async def store_backup_codes(self, user_mfa_id: "object", codes: list[str]) -> None:
        """Hash and store backup codes in the database.

        Parameters
        ----------
        user_mfa_id : uuid.UUID
            The UserMFA record ID.
        codes : list[str]
            Raw backup codes to hash and store.
        """
        for code in codes:
            code_hash = hash_password(code)
            record = MFABackupCode(
                user_mfa_id=user_mfa_id,
                code_hash=code_hash,
                is_used=False,
            )
            self.session.add(record)
        await self.session.flush()

    async def verify_backup_code(self, user_mfa_id: "object", code: str) -> bool:
        """Verify and consume a backup code.

        Parameters
        ----------
        user_mfa_id : uuid.UUID
            The UserMFA record ID.
        code : str
            The backup code to verify.

        Returns
        -------
        bool
            ``True`` if the code was valid and consumed.
        """
        stmt = select(MFABackupCode).where(
            MFABackupCode.user_mfa_id == user_mfa_id,
            MFABackupCode.is_used == False,  # noqa: E712
        )
        result = await self.session.execute(stmt)
        unused_codes = result.scalars().all()

        for record in unused_codes:
            if verify_password(code, record.code_hash):
                record.is_used = True
                await self.session.flush()
                return True
        return False

    # ── Email fallback ────────────────────────────────────────────────

    @staticmethod
    def generate_email_code() -> str:
        """Generate a random 6-digit email verification code.

        Returns
        -------
        str
            Zero-padded 6-digit code.
        """
        return str(secrets.randbelow(1_000_000)).zfill(6)

    async def create_email_code(
        self,
        *,
        user_id: "object",
        email: str,
    ) -> str:
        """Generate and store an email MFA code.

        Parameters
        ----------
        user_id : uuid.UUID
            The user's ID.
        email : str
            Email address to send the code to.

        Returns
        -------
        str
            The 6-digit code (to be sent via email).
        """
        code = self.generate_email_code()
        now = datetime.now(timezone.utc)
        record = MFAEmailCode(
            user_id=user_id,
            email=email,
            code=code,
            expires_at=now + EMAIL_CODE_TTL,
            is_used=False,
        )
        self.session.add(record)
        await self.session.flush()
        return code

    async def verify_email_code(
        self,
        *,
        user_id: "object",
        code: str,
    ) -> bool:
        """Verify an email MFA code.

        Checks the code matches, is not expired, and has not been used.
        Marks the code as used on success.

        Parameters
        ----------
        user_id : uuid.UUID
            The user's ID.
        code : str
            The 6-digit code to verify.

        Returns
        -------
        bool
            ``True`` if the code is valid and consumed.
        """
        now = datetime.now(timezone.utc)
        stmt = select(MFAEmailCode).where(
            MFAEmailCode.user_id == user_id,
            MFAEmailCode.code == code,
            MFAEmailCode.is_used == False,  # noqa: E712
            MFAEmailCode.expires_at > now,
        )
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()

        if record is None:
            return False

        record.is_used = True
        await self.session.flush()
        return True

    async def send_email_code(
        self,
        *,
        user_id: "object",
        email: str,
    ) -> str:
        """Generate, store, and dispatch an email MFA code via Celery.

        Parameters
        ----------
        user_id : uuid.UUID
            The user's ID.
        email : str
            Email address to send the code to.

        Returns
        -------
        str
            The 6-digit code.
        """
        code = await self.create_email_code(user_id=user_id, email=email)

        from shomer.tasks.email import send_email_task

        send_email_task.delay(
            to=email,
            subject="Your MFA verification code",
            template="mfa_code.html",
            context={"code": code},
        )
        return code

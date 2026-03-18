# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""User registration and email verification service."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shomer.core.security import hash_password
from shomer.models.queries import create_user
from shomer.models.user import User
from shomer.models.user_email import UserEmail
from shomer.models.verification_code import VerificationCode

#: Default lifetime for a verification code.
VERIFICATION_CODE_TTL = timedelta(minutes=15)


class DuplicateEmailError(Exception):
    """Raised when the email is already registered."""


class InvalidCodeError(Exception):
    """Raised when the verification code is invalid or expired."""


class EmailNotFoundError(Exception):
    """Raised when the email is not registered."""


class RateLimitError(Exception):
    """Raised when resend is called too frequently."""


#: Minimum interval between resend requests.
RESEND_COOLDOWN = timedelta(minutes=1)


class AuthService:
    """Handle user registration and related flows.

    Attributes
    ----------
    session : AsyncSession
        Database session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def register(
        self,
        *,
        email: str,
        password: str,
        username: str | None = None,
    ) -> tuple[User, str]:
        """Register a new user.

        Creates the user, hashes the password, and generates a
        verification code for the email.

        Parameters
        ----------
        email : str
            Email address (must be unique).
        password : str
            Plain-text password.
        username : str or None
            Optional display name.

        Returns
        -------
        tuple[User, str]
            The created user and the 6-digit verification code.

        Raises
        ------
        DuplicateEmailError
            If the email is already registered.
        """
        # Check uniqueness
        existing = await self._email_exists(email)
        if existing:
            raise DuplicateEmailError(f"Email already registered: {email}")

        # Hash password and create user
        password_hash = hash_password(password)
        user = await create_user(
            self.session,
            email=email,
            password_hash=password_hash,
            username=username,
        )

        # Generate verification code
        code = self._generate_code()
        verification = VerificationCode(
            email=email,
            code=code,
            expires_at=datetime.now(timezone.utc) + VERIFICATION_CODE_TTL,
        )
        self.session.add(verification)
        await self.session.flush()

        return user, code

    async def verify_email(self, *, email: str, code: str) -> None:
        """Verify an email using a 6-digit code.

        Marks the code as used and the email as verified on success.

        Parameters
        ----------
        email : str
            Email address to verify.
        code : str
            Six-digit verification code.

        Raises
        ------
        InvalidCodeError
            If the code is invalid, expired, or already used.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            select(VerificationCode)
            .where(
                VerificationCode.email == email,
                VerificationCode.code == code,
                VerificationCode.used == False,  # noqa: E712
            )
            .order_by(VerificationCode.created_at.desc())
        )
        result = await self.session.execute(stmt)
        vc = result.scalar_one_or_none()

        if vc is None:
            raise InvalidCodeError("Invalid or expired verification code")
        expires_at = vc.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < now:
            raise InvalidCodeError("Invalid or expired verification code")

        # Mark code as used
        vc.used = True

        # Mark email as verified
        email_stmt = select(UserEmail).where(UserEmail.email == email)
        email_result = await self.session.execute(email_stmt)
        user_email = email_result.scalar_one_or_none()
        if user_email is not None:
            user_email.is_verified = True
            user_email.verified_at = now

        await self.session.flush()

    async def resend_code(self, *, email: str) -> str:
        """Generate and return a new verification code for an email.

        Parameters
        ----------
        email : str
            Email address to send a new code to.

        Returns
        -------
        str
            The new 6-digit verification code.

        Raises
        ------
        EmailNotFoundError
            If the email is not registered.
        RateLimitError
            If a code was sent less than ``RESEND_COOLDOWN`` ago.
        """
        # Check email exists
        exists = await self._email_exists(email)
        if not exists:
            raise EmailNotFoundError(f"Email not found: {email}")

        # Rate limit check
        now = datetime.now(timezone.utc)
        cutoff = now - RESEND_COOLDOWN
        recent_stmt = select(VerificationCode).where(
            VerificationCode.email == email,
            VerificationCode.created_at > cutoff,
        )
        recent_result = await self.session.execute(recent_stmt)
        if recent_result.scalar_one_or_none() is not None:
            raise RateLimitError("Please wait before requesting a new code")

        # Generate new code
        code = self._generate_code()
        verification = VerificationCode(
            email=email,
            code=code,
            expires_at=now + VERIFICATION_CODE_TTL,
        )
        self.session.add(verification)
        await self.session.flush()
        return code

    async def _email_exists(self, email: str) -> bool:
        """Check if an email is already registered.

        Parameters
        ----------
        email : str
            Email to check.

        Returns
        -------
        bool
            ``True`` if the email exists.
        """
        stmt = select(UserEmail).where(UserEmail.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    @staticmethod
    def _generate_code() -> str:
        """Generate a 6-digit verification code.

        Returns
        -------
        str
            Zero-padded 6-digit string.
        """
        return f"{secrets.randbelow(1_000_000):06d}"

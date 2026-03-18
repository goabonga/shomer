# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""User registration service."""

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

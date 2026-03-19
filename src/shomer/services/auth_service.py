# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""User registration, email verification, login, and password reset service."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shomer.core.security import hash_password, verify_password
from shomer.models.password_reset_token import PasswordResetToken
from shomer.models.queries import create_user, get_user_by_email
from shomer.models.session import Session
from shomer.models.user import User
from shomer.models.user_email import UserEmail
from shomer.models.user_password import UserPassword
from shomer.models.verification_code import VerificationCode

#: Default lifetime for a verification code.
VERIFICATION_CODE_TTL = timedelta(minutes=15)

#: Default lifetime for a password reset token.
RESET_TOKEN_TTL = timedelta(hours=1)


class DuplicateEmailError(Exception):
    """Raised when the email is already registered."""


class InvalidCodeError(Exception):
    """Raised when the verification code is invalid or expired."""


class EmailNotFoundError(Exception):
    """Raised when the email is not registered."""


class RateLimitError(Exception):
    """Raised when resend is called too frequently."""


class InvalidCredentialsError(Exception):
    """Raised when email or password is incorrect."""


class EmailNotVerifiedError(Exception):
    """Raised when the email has not been verified yet."""


class InvalidResetTokenError(Exception):
    """Raised when the password reset token is invalid or expired."""


#: Minimum interval between resend requests.
RESEND_COOLDOWN = timedelta(minutes=1)

#: Max failed login attempts before lockout.
MAX_LOGIN_ATTEMPTS = 5

#: Lockout duration after max failed attempts.
LOGIN_LOCKOUT_DURATION = timedelta(minutes=15)


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
    ) -> tuple[User | None, str]:
        """Register a new user.

        Creates the user, hashes the password, and generates a
        verification code for the email.

        To prevent user enumeration, this method never raises on
        duplicate emails. Instead it performs a dummy Argon2id hash
        (timing equalization) and returns ``(None, "")``.

        Parameters
        ----------
        email : str
            Email address.
        password : str
            Plain-text password.
        username : str or None
            Optional display name.

        Returns
        -------
        tuple[User | None, str]
            The created user and the 6-digit verification code,
            or ``(None, "")`` if the email already exists.
        """
        # Check uniqueness
        existing = await self._email_exists(email)
        if existing:
            # Dummy hash to equalize timing with the real path
            hash_password("dummy-password")
            return None, ""

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

    async def login(
        self,
        *,
        email: str,
        password: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[User, Session, str]:
        """Authenticate a user and create a session.

        Parameters
        ----------
        email : str
            User email address.
        password : str
            Plain-text password.
        user_agent : str or None
            Browser User-Agent string.
        ip_address : str or None
            Client IP address.

        Returns
        -------
        tuple[User, Session, str]
            The authenticated user, the new session, and the raw
            session token (to be stored in the cookie).

        Raises
        ------
        InvalidCredentialsError
            If the email or password is incorrect.
        EmailNotVerifiedError
            If the email has not been verified.
        """
        user = await get_user_by_email(self.session, email)
        if user is None:
            # Perform a dummy hash to prevent timing-based user enumeration
            hash_password("dummy-password")
            raise InvalidCredentialsError("Invalid email or password")

        # Verify password against current hash (always runs Argon2id)
        current_pw = await self._get_current_password(user.id)
        if current_pw is None or not verify_password(
            password, current_pw.password_hash
        ):
            raise InvalidCredentialsError("Invalid email or password")

        # Check email is verified (only after password is confirmed valid
        # to avoid leaking account existence via different error codes)
        primary_email = next((e for e in user.emails if e.is_primary), None)
        if primary_email is None or not primary_email.is_verified:
            raise EmailNotVerifiedError("Email not verified")

        # Create session
        session_token = uuid.uuid4().hex
        token_hash = hashlib.sha256(session_token.encode()).hexdigest()
        csrf_token = uuid.uuid4().hex
        now = datetime.now(timezone.utc)

        session = Session(
            user_id=user.id,
            token_hash=token_hash,
            csrf_token=csrf_token,
            user_agent=user_agent,
            ip_address=ip_address,
            last_activity=now,
            expires_at=now + timedelta(hours=24),
        )
        self.session.add(session)
        await self.session.flush()

        return user, session, session_token

    async def _get_current_password(self, user_id: uuid.UUID) -> UserPassword | None:
        """Get the current password for a user.

        Parameters
        ----------
        user_id : uuid.UUID
            User primary key.

        Returns
        -------
        UserPassword or None
            The current password record, or ``None``.
        """
        stmt = select(UserPassword).where(
            UserPassword.user_id == user_id,
            UserPassword.is_current == True,  # noqa: E712
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def request_password_reset(self, *, email: str) -> uuid.UUID | None:
        """Generate a password reset token for an email.

        Silently returns ``None`` if the email is not registered (to
        prevent user enumeration).

        Parameters
        ----------
        email : str
            Email address.

        Returns
        -------
        uuid.UUID or None
            The reset token UUID, or ``None`` if email not found.
        """
        user = await get_user_by_email(self.session, email)
        if user is None:
            # Perform a dummy DB query to equalize timing with the
            # real path (token insert + flush). Prevents timing-based
            # user enumeration.
            await self.session.flush()
            return None

        token = PasswordResetToken(
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) + RESET_TOKEN_TTL,
        )
        self.session.add(token)
        await self.session.flush()
        return token.token

    async def verify_password_reset(
        self, *, token: uuid.UUID, new_password: str
    ) -> None:
        """Validate a reset token and set the new password.

        Parameters
        ----------
        token : uuid.UUID
            Reset token UUID from the email link.
        new_password : str
            New plain-text password.

        Raises
        ------
        InvalidResetTokenError
            If the token is invalid, expired, or already used.
        """
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.token == token,
            PasswordResetToken.used == False,  # noqa: E712
        )
        result = await self.session.execute(stmt)
        prt = result.scalar_one_or_none()

        if prt is None:
            raise InvalidResetTokenError("Invalid or expired reset token")

        now = datetime.now(timezone.utc)
        expires_at = prt.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < now:
            raise InvalidResetTokenError("Invalid or expired reset token")

        # Mark token as used
        prt.used = True

        # Deactivate current password and set new one
        current_pw = await self._get_current_password(prt.user_id)
        if current_pw is not None:
            current_pw.is_current = False

        new_pw = UserPassword(
            user_id=prt.user_id,
            password_hash=hash_password(new_password),
        )
        self.session.add(new_pw)
        await self.session.flush()

    async def change_password(
        self,
        *,
        user_id: uuid.UUID,
        current_password: str,
        new_password: str,
    ) -> None:
        """Change a user's password after verifying the current one.

        Parameters
        ----------
        user_id : uuid.UUID
            Authenticated user's ID.
        current_password : str
            Current plain-text password.
        new_password : str
            New plain-text password.

        Raises
        ------
        InvalidCredentialsError
            If the current password is incorrect.
        """
        current_pw = await self._get_current_password(user_id)
        if current_pw is None or not verify_password(
            current_password, current_pw.password_hash
        ):
            raise InvalidCredentialsError("Current password is incorrect")

        current_pw.is_current = False
        new_pw = UserPassword(
            user_id=user_id,
            password_hash=hash_password(new_password),
        )
        self.session.add(new_pw)
        await self.session.flush()

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

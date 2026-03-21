# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Device Authorization service per RFC 8628.

Manages the device authorization flow lifecycle: code generation,
user approval/denial, polling, and expiration.
"""

from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from shomer.models.device_code import DeviceCode, DeviceCodeStatus

#: Default device code expiration in seconds (15 minutes).
DEVICE_CODE_EXPIRES = 900

#: Default polling interval in seconds.
DEFAULT_INTERVAL = 5

#: Characters for human-friendly user codes (no ambiguous chars).
_USER_CODE_CHARS = "BCDFGHJKLMNPQRSTVWXZ"


class DeviceAuthError(Exception):
    """Error during device authorization flow.

    Attributes
    ----------
    error : str
        RFC 8628 error code.
    description : str
        Human-readable description.
    """

    def __init__(self, error: str, description: str) -> None:
        self.error = error
        self.description = description
        super().__init__(description)


@dataclass
class DeviceAuthResponse:
    """Response from device authorization request.

    Attributes
    ----------
    device_code : str
        The device verification code.
    user_code : str
        The end-user verification code.
    verification_uri : str
        URI for user to visit.
    verification_uri_complete : str or None
        URI with user_code pre-filled.
    expires_in : int
        Lifetime in seconds.
    interval : int
        Minimum polling interval in seconds.
    """

    device_code: str
    user_code: str
    verification_uri: str
    verification_uri_complete: str | None = None
    expires_in: int = DEVICE_CODE_EXPIRES
    interval: int = DEFAULT_INTERVAL


class DeviceAuthService:
    """Manage device authorization flow lifecycle.

    Attributes
    ----------
    session : AsyncSession
        Database session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_device_code(
        self,
        *,
        client_id: str,
        scopes: str,
        verification_uri: str,
    ) -> DeviceAuthResponse:
        """Create a new device authorization request.

        Parameters
        ----------
        client_id : str
            The OAuth2 client identifier.
        scopes : str
            Space-separated requested scopes.
        verification_uri : str
            Base URI where user enters the code.

        Returns
        -------
        DeviceAuthResponse
            The device code response to return to the client.
        """
        device_code = secrets.token_urlsafe(32)
        user_code = self._generate_user_code()
        now = datetime.now(timezone.utc)

        verification_uri_complete = f"{verification_uri}?user_code={user_code}"

        dc = DeviceCode(
            device_code=device_code,
            user_code=user_code,
            client_id=client_id,
            scopes=scopes,
            verification_uri=verification_uri,
            verification_uri_complete=verification_uri_complete,
            interval=DEFAULT_INTERVAL,
            status=DeviceCodeStatus.PENDING,
            expires_at=now + timedelta(seconds=DEVICE_CODE_EXPIRES),
        )
        self.session.add(dc)
        await self.session.flush()

        return DeviceAuthResponse(
            device_code=device_code,
            user_code=user_code,
            verification_uri=verification_uri,
            verification_uri_complete=verification_uri_complete,
            expires_in=DEVICE_CODE_EXPIRES,
            interval=DEFAULT_INTERVAL,
        )

    async def approve(self, *, user_code: str, user_id: uuid.UUID) -> DeviceCode:
        """Approve a device authorization by user_code.

        Parameters
        ----------
        user_code : str
            The user-facing code.
        user_id : uuid.UUID
            The authenticated user approving the request.

        Returns
        -------
        DeviceCode
            The updated device code record.

        Raises
        ------
        DeviceAuthError
            If the code is invalid, expired, or not pending.
        """
        dc = await self._get_pending_code(user_code)
        dc.status = DeviceCodeStatus.APPROVED
        dc.user_id = user_id
        await self.session.flush()
        return dc

    async def deny(self, *, user_code: str) -> DeviceCode:
        """Deny a device authorization by user_code.

        Parameters
        ----------
        user_code : str
            The user-facing code.

        Returns
        -------
        DeviceCode
            The updated device code record.

        Raises
        ------
        DeviceAuthError
            If the code is invalid, expired, or not pending.
        """
        dc = await self._get_pending_code(user_code)
        dc.status = DeviceCodeStatus.DENIED
        await self.session.flush()
        return dc

    async def check_status(self, *, device_code: str) -> DeviceCode:
        """Check the current status of a device authorization.

        Parameters
        ----------
        device_code : str
            The device code (from the client polling).

        Returns
        -------
        DeviceCode
            The device code record.

        Raises
        ------
        DeviceAuthError
            If the code is unknown or expired.
        """
        stmt = select(DeviceCode).where(DeviceCode.device_code == device_code)
        result = await self.session.execute(stmt)
        dc = result.scalar_one_or_none()

        if dc is None:
            raise DeviceAuthError("invalid_grant", "Unknown device code")

        now = datetime.now(timezone.utc)
        expires_at = dc.expires_at
        if expires_at.tzinfo is None:  # pragma: no cover
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < now:
            if dc.status == DeviceCodeStatus.PENDING:
                dc.status = DeviceCodeStatus.EXPIRED
                await self.session.flush()
            raise DeviceAuthError("expired_token", "Device code has expired")

        return dc

    async def expire_old_codes(self) -> int:
        """Mark all expired pending codes as expired.

        Returns
        -------
        int
            Number of codes expired.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            update(DeviceCode)
            .where(
                DeviceCode.status == DeviceCodeStatus.PENDING,
                DeviceCode.expires_at < now,
            )
            .values(status=DeviceCodeStatus.EXPIRED)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount  # type: ignore[no-any-return,attr-defined]

    async def _get_pending_code(self, user_code: str) -> DeviceCode:
        """Look up a pending device code by user_code.

        Parameters
        ----------
        user_code : str
            The user-facing code.

        Returns
        -------
        DeviceCode

        Raises
        ------
        DeviceAuthError
            If not found, expired, or not pending.
        """
        stmt = select(DeviceCode).where(DeviceCode.user_code == user_code)
        result = await self.session.execute(stmt)
        dc = result.scalar_one_or_none()

        if dc is None:
            raise DeviceAuthError("invalid_grant", "Unknown user code")

        now = datetime.now(timezone.utc)
        expires_at = dc.expires_at
        if expires_at.tzinfo is None:  # pragma: no cover
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < now:
            raise DeviceAuthError("expired_token", "Device code has expired")

        if dc.status != DeviceCodeStatus.PENDING:
            raise DeviceAuthError(
                "invalid_grant",
                f"Device code is {dc.status.value}, not pending",
            )

        return dc

    @staticmethod
    def _generate_user_code() -> str:
        """Generate a human-friendly user code (XXXX-XXXX).

        Uses consonants only (no ambiguous characters like O/0, I/1).

        Returns
        -------
        str
            An 8-character code in XXXX-XXXX format.
        """
        part1 = "".join(secrets.choice(_USER_CODE_CHARS) for _ in range(4))
        part2 = "".join(secrets.choice(_USER_CODE_CHARS) for _ in range(4))
        return f"{part1}-{part2}"

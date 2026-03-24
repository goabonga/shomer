# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Personal Access Token service.

Manages PAT lifecycle: creation (with ``shm_pat_`` prefix), validation
by hash lookup, revocation, and last-used tracking.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shomer.models.personal_access_token import PAT_PREFIX, PersonalAccessToken


class PATError(Exception):
    """Raised when a PAT operation fails.

    Attributes
    ----------
    message : str
        Human-readable error description.
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


@dataclass
class PATCreateResult:
    """Result of PAT creation — includes the raw token shown once.

    Attributes
    ----------
    id : uuid.UUID
        The PAT record ID.
    name : str
        Human-readable label.
    token : str
        The full raw token (shown once, never stored).
    token_prefix : str
        First characters for display (``shm_pat_...``).
    scopes : str
        Space-separated scopes.
    expires_at : datetime or None
        Expiration timestamp.
    created_at : datetime
        Creation timestamp.
    """

    id: uuid.UUID
    name: str
    token: str
    token_prefix: str
    scopes: str
    expires_at: datetime | None
    created_at: datetime


@dataclass
class PATInfo:
    """PAT metadata (no raw token value).

    Attributes
    ----------
    id : uuid.UUID
        The PAT record ID.
    name : str
        Human-readable label.
    token_prefix : str
        First characters for display.
    scopes : str
        Space-separated scopes.
    expires_at : datetime or None
        Expiration timestamp.
    last_used_at : datetime or None
        Last usage timestamp.
    is_revoked : bool
        Whether the token is revoked.
    created_at : datetime
        Creation timestamp.
    """

    id: uuid.UUID
    name: str
    token_prefix: str
    scopes: str
    expires_at: datetime | None
    last_used_at: datetime | None
    is_revoked: bool
    created_at: datetime


class PATService:
    """Manage Personal Access Token lifecycle.

    Attributes
    ----------
    session : AsyncSession
        Database session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        name: str,
        scopes: str = "",
        expires_at: datetime | None = None,
    ) -> PATCreateResult:
        """Create a new Personal Access Token.

        Generates a secure random token with ``shm_pat_`` prefix,
        hashes it with SHA-256, and stores the hash. The raw token
        is returned only once.

        Parameters
        ----------
        user_id : uuid.UUID
            The token owner's ID.
        name : str
            Human-readable label.
        scopes : str
            Space-separated scopes for this token.
        expires_at : datetime or None
            Optional expiration.

        Returns
        -------
        PATCreateResult
            The created PAT including the raw token (shown once).
        """
        raw_secret = secrets.token_urlsafe(32)
        raw_token = f"{PAT_PREFIX}{raw_secret}"
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        token_prefix = raw_token[:16]

        now = datetime.now(timezone.utc)
        pat = PersonalAccessToken(
            user_id=user_id,
            name=name,
            token_prefix=token_prefix,
            token_hash=token_hash,
            scopes=scopes,
            expires_at=expires_at,
            is_revoked=False,
        )
        self.session.add(pat)
        await self.session.flush()

        return PATCreateResult(
            id=pat.id,
            name=name,
            token=raw_token,
            token_prefix=token_prefix,
            scopes=scopes,
            expires_at=expires_at,
            created_at=now,
        )

    async def validate(self, raw_token: str) -> PersonalAccessToken:
        """Validate a PAT by hash lookup.

        Checks that the token exists, is not revoked, and has not
        expired. Updates ``last_used_at`` on success.

        Parameters
        ----------
        raw_token : str
            The full raw token (``shm_pat_...``).

        Returns
        -------
        PersonalAccessToken
            The validated token record.

        Raises
        ------
        PATError
            If the token is invalid, revoked, or expired.
        """
        if not raw_token.startswith(PAT_PREFIX):
            raise PATError("Invalid token format")

        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        stmt = select(PersonalAccessToken).where(
            PersonalAccessToken.token_hash == token_hash,
        )
        result = await self.session.execute(stmt)
        pat = result.scalar_one_or_none()

        if pat is None:
            raise PATError("Invalid token")

        if pat.is_revoked:
            raise PATError("Token has been revoked")

        now = datetime.now(timezone.utc)
        if pat.expires_at is not None and pat.expires_at < now:
            raise PATError("Token has expired")

        # Track usage
        pat.last_used_at = now
        await self.session.flush()

        return pat

    async def revoke(self, pat_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Revoke a PAT.

        Parameters
        ----------
        pat_id : uuid.UUID
            The PAT record ID.
        user_id : uuid.UUID
            The token owner's ID (authorization check).

        Raises
        ------
        PATError
            If the PAT is not found or doesn't belong to the user.
        """
        stmt = select(PersonalAccessToken).where(
            PersonalAccessToken.id == pat_id,
            PersonalAccessToken.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        pat = result.scalar_one_or_none()

        if pat is None:
            raise PATError("Token not found")

        pat.is_revoked = True
        await self.session.flush()

    async def regenerate(
        self,
        pat_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> PATCreateResult:
        """Regenerate a PAT: revoke the old token and create a new one.

        The new token inherits the name, scopes, and expiration of the
        original. The old token is revoked immediately.

        Parameters
        ----------
        pat_id : uuid.UUID
            The existing PAT record ID to regenerate.
        user_id : uuid.UUID
            The token owner's ID (authorization check).

        Returns
        -------
        PATCreateResult
            The newly created PAT including the raw token (shown once).

        Raises
        ------
        PATError
            If the PAT is not found or doesn't belong to the user.
        """
        stmt = select(PersonalAccessToken).where(
            PersonalAccessToken.id == pat_id,
            PersonalAccessToken.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        pat = result.scalar_one_or_none()

        if pat is None:
            raise PATError("Token not found")

        # Capture original attributes before revoking
        name = pat.name
        scopes = pat.scopes
        expires_at = pat.expires_at

        # Revoke old token
        pat.is_revoked = True
        await self.session.flush()

        # Create replacement with same attributes
        return await self.create(
            user_id=user_id,
            name=name,
            scopes=scopes,
            expires_at=expires_at,
        )

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> int:
        """Revoke all active PATs for a user.

        Parameters
        ----------
        user_id : uuid.UUID
            The token owner's ID.

        Returns
        -------
        int
            Number of tokens revoked.
        """
        stmt = select(PersonalAccessToken).where(
            PersonalAccessToken.user_id == user_id,
            PersonalAccessToken.is_revoked.is_(False),
        )
        result = await self.session.execute(stmt)
        pats = result.scalars().all()

        for pat in pats:
            pat.is_revoked = True

        await self.session.flush()
        return len(pats)

    async def list_for_user(self, user_id: uuid.UUID) -> list[PATInfo]:
        """List all PATs for a user (metadata only).

        Parameters
        ----------
        user_id : uuid.UUID
            The user's ID.

        Returns
        -------
        list[PATInfo]
            PAT metadata without raw token values.
        """
        stmt = (
            select(PersonalAccessToken)
            .where(PersonalAccessToken.user_id == user_id)
            .order_by(PersonalAccessToken.created_at.desc())
        )
        result = await self.session.execute(stmt)
        pats = result.scalars().all()

        return [
            PATInfo(
                id=p.id,
                name=p.name,
                token_prefix=p.token_prefix,
                scopes=p.scopes,
                expires_at=p.expires_at,
                last_used_at=p.last_used_at,
                is_revoked=p.is_revoked,
                created_at=p.created_at,
            )
            for p in pats
        ]

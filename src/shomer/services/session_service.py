# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Browser session management service."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from shomer.models.session import Session

#: Default session lifetime.
SESSION_TTL = timedelta(hours=24)

#: Sliding window extension on each renewal.
SESSION_RENEWAL_WINDOW = timedelta(hours=1)


class SessionService:
    """Manage browser sessions: create, validate, renew, delete.

    Attributes
    ----------
    db : AsyncSession
        Database session.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        user_agent: str | None = None,
        ip_address: str | None = None,
        tenant_id: uuid.UUID | None = None,
    ) -> tuple[Session, str]:
        """Create a new browser session.

        Parameters
        ----------
        user_id : uuid.UUID
            Owner of the session.
        user_agent : str or None
            Browser User-Agent string.
        ip_address : str or None
            Client IP address.
        tenant_id : uuid.UUID or None
            Optional tenant identifier.

        Returns
        -------
        tuple[Session, str]
            The persisted session and the raw (unhashed) token.
        """
        raw_token = uuid.uuid4().hex
        token_hash = self._hash_token(raw_token)
        csrf_token = uuid.uuid4().hex
        now = datetime.now(timezone.utc)

        session = Session(
            user_id=user_id,
            tenant_id=tenant_id,
            token_hash=token_hash,
            csrf_token=csrf_token,
            user_agent=user_agent,
            ip_address=ip_address,
            last_activity=now,
            expires_at=now + SESSION_TTL,
        )
        self.db.add(session)
        await self.db.flush()
        return session, raw_token

    async def validate(self, token: str) -> Session | None:
        """Look up and validate a session by its raw token.

        Returns ``None`` if the session does not exist or has expired.

        Parameters
        ----------
        token : str
            Raw session token (from the cookie).

        Returns
        -------
        Session or None
            The valid session, or ``None``.
        """
        token_hash = self._hash_token(token)
        stmt = select(Session).where(Session.token_hash == token_hash)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if session is None:
            return None

        now = datetime.now(timezone.utc)
        expires_at = session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < now:
            return None

        return session

    async def renew(self, session: Session) -> Session:
        """Extend the session expiration (sliding window).

        Parameters
        ----------
        session : Session
            The session to renew.

        Returns
        -------
        Session
            The renewed session.
        """
        now = datetime.now(timezone.utc)
        session.last_activity = now
        session.expires_at = now + SESSION_RENEWAL_WINDOW
        await self.db.flush()
        return session

    async def delete(self, session_id: uuid.UUID) -> bool:
        """Delete a single session.

        Parameters
        ----------
        session_id : uuid.UUID
            ID of the session to delete.

        Returns
        -------
        bool
            ``True`` if the session was deleted.
        """
        stmt = delete(Session).where(Session.id == session_id)
        result = await self.db.execute(stmt)
        await self.db.flush()
        rc: int = getattr(result, "rowcount", 0) or 0
        return rc > 0

    async def delete_all_for_user(self, user_id: uuid.UUID) -> int:
        """Delete all sessions for a user.

        Parameters
        ----------
        user_id : uuid.UUID
            User whose sessions should be deleted.

        Returns
        -------
        int
            Number of sessions deleted.
        """
        stmt = delete(Session).where(Session.user_id == user_id)
        result = await self.db.execute(stmt)
        await self.db.flush()
        rc: int = getattr(result, "rowcount", 0) or 0
        return rc

    async def delete_all_for_user_except(
        self, user_id: uuid.UUID, exclude_session_id: uuid.UUID
    ) -> int:
        """Delete all sessions for a user except the specified one.

        Parameters
        ----------
        user_id : uuid.UUID
            User whose sessions should be deleted.
        exclude_session_id : uuid.UUID
            Session ID to keep (typically the current session).

        Returns
        -------
        int
            Number of sessions deleted.
        """
        stmt = delete(Session).where(
            Session.user_id == user_id,
            Session.id != exclude_session_id,
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        rc: int = getattr(result, "rowcount", 0) or 0
        return rc

    async def list_active(self, user_id: uuid.UUID) -> list[Session]:
        """List all active (non-expired) sessions for a user.

        Parameters
        ----------
        user_id : uuid.UUID
            User ID.

        Returns
        -------
        list[Session]
            Active sessions ordered by last activity (most recent first).
        """
        now = datetime.now(timezone.utc)
        stmt = (
            select(Session)
            .where(
                Session.user_id == user_id,
                Session.expires_at > now,
            )
            .order_by(Session.last_activity.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def _hash_token(token: str) -> str:
        """Hash a raw session token with SHA-256.

        Parameters
        ----------
        token : str
            Raw token string.

        Returns
        -------
        str
            Hex-encoded SHA-256 hash.
        """
        return hashlib.sha256(token.encode()).hexdigest()

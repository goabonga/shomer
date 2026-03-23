# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Celery Beat tasks for cleaning up expired database records.

Each task deletes records that have passed their ``expires_at``
timestamp, using batch deletion with a configurable limit.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select

from shomer.worker import app

logger = logging.getLogger(__name__)

#: Default batch size for deletion queries.
DEFAULT_BATCH_SIZE = 1000


def _run_sync_cleanup(model_cls: Any, label: str, batch_size: int) -> int:
    """Run a synchronous cleanup for a model with ``expires_at``.

    Uses a synchronous database session (Celery tasks run outside
    the async event loop).

    Parameters
    ----------
    model_cls : type
        SQLAlchemy model class with an ``expires_at`` column.
    label : str
        Human-readable label for logging.
    batch_size : int
        Maximum number of records to delete per run.

    Returns
    -------
    int
        Number of deleted records.
    """
    from shomer.core.database import sync_session

    now = datetime.now(timezone.utc)

    with sync_session() as session:
        # Select IDs to delete (batch limited)
        ids_stmt = (
            select(model_cls.id).where(model_cls.expires_at <= now).limit(batch_size)
        )
        result = session.execute(ids_stmt)
        ids_to_delete = [row[0] for row in result.fetchall()]

        if not ids_to_delete:
            logger.info("[cleanup] %s: 0 expired records", label)
            return 0

        del_stmt = delete(model_cls).where(model_cls.id.in_(ids_to_delete))
        session.execute(del_stmt)
        session.commit()

        count = len(ids_to_delete)
        logger.info("[cleanup] %s: deleted %d expired records", label, count)
        return count


def _run_sync_cleanup_revoked(model_cls: Any, label: str, batch_size: int) -> int:
    """Run a synchronous cleanup for revoked PATs.

    Parameters
    ----------
    model_cls : type
        SQLAlchemy model class with ``is_revoked`` column.
    label : str
        Human-readable label for logging.
    batch_size : int
        Maximum number of records to delete per run.

    Returns
    -------
    int
        Number of deleted records.
    """
    from shomer.core.database import sync_session

    with sync_session() as session:
        ids_stmt = (
            select(model_cls.id)
            .where(model_cls.is_revoked == True)  # noqa: E712
            .limit(batch_size)
        )
        result = session.execute(ids_stmt)
        ids_to_delete = [row[0] for row in result.fetchall()]

        if not ids_to_delete:
            logger.info("[cleanup] %s: 0 revoked records", label)
            return 0

        del_stmt = delete(model_cls).where(model_cls.id.in_(ids_to_delete))
        session.execute(del_stmt)
        session.commit()

        count = len(ids_to_delete)
        logger.info("[cleanup] %s: deleted %d revoked records", label, count)
        return count


@app.task(name="shomer.cleanup.access_tokens")  # type: ignore[misc]
def clean_expired_access_tokens(batch_size: int = DEFAULT_BATCH_SIZE) -> int:
    """Delete expired access tokens.

    Parameters
    ----------
    batch_size : int
        Max records to delete per run.

    Returns
    -------
    int
        Number of deleted records.
    """
    from shomer.models.access_token import AccessToken

    return _run_sync_cleanup(AccessToken, "AccessToken", batch_size)


@app.task(name="shomer.cleanup.refresh_tokens")  # type: ignore[misc]
def clean_expired_refresh_tokens(batch_size: int = DEFAULT_BATCH_SIZE) -> int:
    """Delete expired refresh tokens.

    Parameters
    ----------
    batch_size : int
        Max records to delete per run.

    Returns
    -------
    int
        Number of deleted records.
    """
    from shomer.models.refresh_token import RefreshToken

    return _run_sync_cleanup(RefreshToken, "RefreshToken", batch_size)


@app.task(name="shomer.cleanup.authorization_codes")  # type: ignore[misc]
def clean_expired_authorization_codes(batch_size: int = DEFAULT_BATCH_SIZE) -> int:
    """Delete expired authorization codes.

    Parameters
    ----------
    batch_size : int
        Max records to delete per run.

    Returns
    -------
    int
        Number of deleted records.
    """
    from shomer.models.authorization_code import AuthorizationCode

    return _run_sync_cleanup(AuthorizationCode, "AuthorizationCode", batch_size)


@app.task(name="shomer.cleanup.device_codes")  # type: ignore[misc]
def clean_expired_device_codes(batch_size: int = DEFAULT_BATCH_SIZE) -> int:
    """Delete expired device codes.

    Parameters
    ----------
    batch_size : int
        Max records to delete per run.

    Returns
    -------
    int
        Number of deleted records.
    """
    from shomer.models.device_code import DeviceCode

    return _run_sync_cleanup(DeviceCode, "DeviceCode", batch_size)


@app.task(name="shomer.cleanup.par_requests")  # type: ignore[misc]
def clean_expired_par_requests(batch_size: int = DEFAULT_BATCH_SIZE) -> int:
    """Delete expired PAR requests.

    Parameters
    ----------
    batch_size : int
        Max records to delete per run.

    Returns
    -------
    int
        Number of deleted records.
    """
    from shomer.models.par_request import PARRequest

    return _run_sync_cleanup(PARRequest, "PARRequest", batch_size)


@app.task(name="shomer.cleanup.verification_codes")  # type: ignore[misc]
def clean_expired_verification_codes(batch_size: int = DEFAULT_BATCH_SIZE) -> int:
    """Delete expired verification codes and password reset tokens.

    Parameters
    ----------
    batch_size : int
        Max records to delete per run.

    Returns
    -------
    int
        Total number of deleted records.
    """
    from shomer.models.password_reset_token import PasswordResetToken
    from shomer.models.verification_code import VerificationCode

    count = _run_sync_cleanup(VerificationCode, "VerificationCode", batch_size)
    count += _run_sync_cleanup(PasswordResetToken, "PasswordResetToken", batch_size)
    return count


@app.task(name="shomer.cleanup.sessions")  # type: ignore[misc]
def clean_expired_sessions(batch_size: int = DEFAULT_BATCH_SIZE) -> int:
    """Delete expired sessions.

    Parameters
    ----------
    batch_size : int
        Max records to delete per run.

    Returns
    -------
    int
        Number of deleted records.
    """
    from shomer.models.session import Session

    return _run_sync_cleanup(Session, "Session", batch_size)


@app.task(name="shomer.cleanup.mfa_codes")  # type: ignore[misc]
def clean_expired_mfa_codes(batch_size: int = DEFAULT_BATCH_SIZE) -> int:
    """Delete expired MFA email codes.

    Parameters
    ----------
    batch_size : int
        Max records to delete per run.

    Returns
    -------
    int
        Number of deleted records.
    """
    from shomer.models.mfa_email_code import MFAEmailCode

    return _run_sync_cleanup(MFAEmailCode, "MFAEmailCode", batch_size)


@app.task(name="shomer.cleanup.revoked_pats")  # type: ignore[misc]
def clean_revoked_pats(batch_size: int = DEFAULT_BATCH_SIZE) -> int:
    """Delete revoked personal access tokens.

    Parameters
    ----------
    batch_size : int
        Max records to delete per run.

    Returns
    -------
    int
        Number of deleted records.
    """
    from shomer.models.personal_access_token import PersonalAccessToken

    return _run_sync_cleanup_revoked(PersonalAccessToken, "RevokedPAT", batch_size)

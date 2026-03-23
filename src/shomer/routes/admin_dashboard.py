# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Admin dashboard endpoint returning aggregate system statistics.

Requires the ``admin:dashboard:read`` scope.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import func, select

from shomer.deps import DbSession
from shomer.middleware.rbac import require_scope
from shomer.models.access_token import AccessToken
from shomer.models.oauth2_client import OAuth2Client
from shomer.models.session import Session
from shomer.models.user import User
from shomer.models.user_email import UserEmail
from shomer.models.user_mfa import UserMFA

router = APIRouter(prefix="/admin/dashboard", tags=["admin"])


@router.get(
    "",
    dependencies=[Depends(require_scope("admin:dashboard:read"))],
)
async def dashboard(db: DbSession) -> JSONResponse:
    """Return aggregate system statistics for the admin dashboard.

    Parameters
    ----------
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Dashboard statistics including users, sessions, clients,
        tokens, and MFA adoption.
    """
    now = datetime.now(timezone.utc)
    last_24h = now - timedelta(hours=24)

    # User statistics
    total_users_result = await db.execute(select(func.count()).select_from(User))
    total_users = total_users_result.scalar() or 0

    active_users_result = await db.execute(
        select(func.count()).select_from(User).where(User.is_active == True)  # noqa: E712
    )
    active_users = active_users_result.scalar() or 0

    verified_emails_result = await db.execute(
        select(func.count(func.distinct(UserEmail.user_id))).where(
            UserEmail.is_verified == True  # noqa: E712
        )
    )
    verified_users = verified_emails_result.scalar() or 0

    # Session statistics
    active_sessions_result = await db.execute(
        select(func.count()).select_from(Session).where(Session.expires_at > now)
    )
    active_sessions = active_sessions_result.scalar() or 0

    # Client statistics
    total_clients_result = await db.execute(
        select(func.count()).select_from(OAuth2Client)
    )
    total_clients = total_clients_result.scalar() or 0

    confidential_clients_result = await db.execute(
        select(func.count())
        .select_from(OAuth2Client)
        .where(OAuth2Client.client_type == "CONFIDENTIAL")
    )
    confidential_clients = confidential_clients_result.scalar() or 0

    public_clients = total_clients - confidential_clients

    # Token statistics (last 24h)
    tokens_24h_result = await db.execute(
        select(func.count())
        .select_from(AccessToken)
        .where(AccessToken.created_at > last_24h)
    )
    tokens_issued_24h = tokens_24h_result.scalar() or 0

    # MFA adoption
    mfa_enabled_result = await db.execute(
        select(func.count()).select_from(UserMFA).where(UserMFA.is_enabled == True)  # noqa: E712
    )
    mfa_enabled = mfa_enabled_result.scalar() or 0

    mfa_adoption_rate = (
        round(mfa_enabled / total_users * 100, 1) if total_users > 0 else 0.0
    )

    return JSONResponse(
        content={
            "users": {
                "total": total_users,
                "active": active_users,
                "verified": verified_users,
            },
            "sessions": {
                "active": active_sessions,
            },
            "clients": {
                "total": total_clients,
                "confidential": confidential_clients,
                "public": public_clients,
            },
            "tokens": {
                "issued_24h": tokens_issued_24h,
            },
            "mfa": {
                "enabled": mfa_enabled,
                "adoption_rate": mfa_adoption_rate,
            },
        }
    )

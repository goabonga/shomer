# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Browser-facing connected applications UI route (Jinja2/HTMX).

Lists OAuth2 applications the user has authorized (via consent) and
allows revoking access, within the user settings area.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, update

from shomer.deps import DbSession
from shomer.models.access_token import AccessToken
from shomer.models.oauth2_client import OAuth2Client
from shomer.services.session_service import SessionService

router = APIRouter(prefix="/ui/settings", tags=["ui"], include_in_schema=False)


def _templates() -> Jinja2Templates:
    """Get the Jinja2 templates instance."""
    from shomer.app import templates

    return templates


def _render(request: Request, template: str, ctx: dict[str, Any] | None = None) -> Any:
    """Render a template with the given context.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    template : str
        Template path relative to the templates directory.
    ctx : dict or None
        Template context variables.

    Returns
    -------
    Any
        Jinja2 TemplateResponse.
    """
    return _templates().TemplateResponse(request, template, ctx or {})


async def _get_session_user_id(request: Request, db: Any) -> Any:
    """Validate session and return user_id or None.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : AsyncSession
        Database session.

    Returns
    -------
    uuid.UUID or None
        The authenticated user ID, or None.
    """
    session_token = request.cookies.get("session_id")
    if not session_token:
        return None
    svc = SessionService(db)
    session = await svc.validate(session_token)
    return session.user_id if session else None


async def _fetch_authorized_apps(db: Any, user_id: uuid.UUID) -> list[dict[str, Any]]:
    """Fetch authorized OAuth2 applications for a user.

    Groups access tokens by client_id and merges scopes across tokens
    for the same client.

    Parameters
    ----------
    db : AsyncSession
        Database session.
    user_id : uuid.UUID
        The user whose authorized apps to fetch.

    Returns
    -------
    list[dict]
        List of app dicts with client_id, client_name, logo_uri,
        scopes, and authorized_at.
    """
    stmt = (
        select(
            OAuth2Client.client_id,
            OAuth2Client.client_name,
            OAuth2Client.logo_uri,
            AccessToken.scopes,
            AccessToken.created_at,
        )
        .join(OAuth2Client, AccessToken.client_id == OAuth2Client.client_id)
        .where(
            AccessToken.user_id == user_id,
            AccessToken.revoked == False,  # noqa: E712
        )
        .order_by(AccessToken.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    seen: dict[str, dict[str, Any]] = {}
    for row in rows:
        cid = row.client_id
        if cid not in seen:
            seen[cid] = {
                "client_id": cid,
                "client_name": row.client_name,
                "logo_uri": row.logo_uri,
                "scopes": set(row.scopes.split()) if row.scopes else set(),
                "authorized_at": row.created_at.isoformat(),
            }
        else:
            if row.scopes:
                seen[cid]["scopes"].update(row.scopes.split())

    apps = []
    for entry in seen.values():
        apps.append(
            {
                "client_id": entry["client_id"],
                "client_name": entry["client_name"],
                "logo_uri": entry["logo_uri"],
                "scopes": " ".join(sorted(entry["scopes"])),
                "authorized_at": entry["authorized_at"],
            }
        )
    return apps


@router.get("/applications", response_class=HTMLResponse)
async def applications_page(request: Request, db: DbSession) -> Any:
    """Render the connected applications page.

    Lists distinct OAuth2 clients the user has authorized, showing
    client name, granted scopes, and authorization date.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.

    Returns
    -------
    HTMLResponse
        Connected applications page or redirect to login.
    """
    user_id = await _get_session_user_id(request, db)
    if user_id is None:
        return RedirectResponse(
            url="/ui/login?next=/ui/settings/applications", status_code=302
        )

    apps = await _fetch_authorized_apps(db, user_id)

    return _render(
        request,
        "settings/applications.html",
        {
            "apps": apps,
            "success": None,
            "error": None,
        },
    )


@router.post("/applications", response_class=HTMLResponse)
async def applications_action(
    request: Request,
    db: DbSession,
    action: str = Form(""),
    client_id: str = Form(""),
) -> Any:
    """Handle connected-applications form submissions (revoke).

    Revokes all active access tokens for the given client_id
    belonging to the authenticated user.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.
    action : str
        Form action (``revoke``).
    client_id : str
        The OAuth2 client_id to revoke access for.

    Returns
    -------
    HTMLResponse
        Updated applications page with success/error message.
    """
    user_id = await _get_session_user_id(request, db)
    if user_id is None:
        return RedirectResponse(
            url="/ui/login?next=/ui/settings/applications", status_code=302
        )

    error = None
    success = None

    if action == "revoke":
        if not client_id:
            error = "No application specified."
        else:
            stmt = (
                update(AccessToken)
                .where(
                    AccessToken.user_id == user_id,
                    AccessToken.client_id == client_id,
                    AccessToken.revoked == False,  # noqa: E712
                )
                .values(revoked=True)
            )
            result = await db.execute(stmt)
            row_count: int = getattr(result, "rowcount", 0)
            if row_count > 0:
                await db.flush()
                success = "Application access revoked."
            else:
                error = "No active access found for this application."

    apps = await _fetch_authorized_apps(db, user_id)

    return _render(
        request,
        "settings/applications.html",
        {
            "apps": apps,
            "success": success,
            "error": error,
        },
    )

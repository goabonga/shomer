# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Browser-facing PAT management UI route (Jinja2/HTMX).

Personal access token listing, creation, and revocation page
within the user settings area.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from shomer.deps import DbSession
from shomer.services.pat_service import PATError, PATService
from shomer.services.session_service import SessionService

router = APIRouter(prefix="/ui/settings", tags=["ui"], include_in_schema=False)


def _templates() -> Jinja2Templates:
    """Get the Jinja2 templates instance."""
    from shomer.app import templates

    return templates


def _render(request: Request, template: str, ctx: dict[str, Any] | None = None) -> Any:
    """Render a template with the given context."""
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


@router.get("/pats", response_class=HTMLResponse)
async def pat_list_page(request: Request, db: DbSession) -> Any:
    """Render the PAT management page with existing tokens.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.

    Returns
    -------
    HTMLResponse
        PAT management page or redirect to login.
    """
    user_id = await _get_session_user_id(request, db)
    if user_id is None:
        return RedirectResponse(url="/ui/login?next=/ui/settings/pats", status_code=302)

    svc = PATService(db)
    pats = await svc.list_for_user(user_id)

    tokens = [
        {
            "id": str(p.id),
            "name": p.name,
            "token_prefix": p.token_prefix,
            "scopes": p.scopes,
            "expires_at": p.expires_at.isoformat() if p.expires_at else None,
            "last_used_at": p.last_used_at.isoformat() if p.last_used_at else None,
            "last_used_ip": p.last_used_ip,
            "use_count": p.use_count,
            "is_revoked": p.is_revoked,
        }
        for p in pats
    ]

    return _render(request, "settings/pats.html", {"tokens": tokens})


@router.post("/pats", response_class=HTMLResponse)
async def pat_action(
    request: Request,
    db: DbSession,
    action: str = Form("create"),
    name: str = Form(""),
    scopes: str = Form(""),
    expires_at: str = Form(""),
    pat_id: str = Form(""),
) -> Any:
    """Handle PAT create/revoke/regenerate form submissions.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.
    action : str
        ``create``, ``revoke``, or ``regenerate``.
    name : str
        Token name (for create).
    scopes : str
        Space-separated scopes (for create).
    expires_at : str
        Expiration date string (for create).
    pat_id : str
        PAT ID (for revoke or regenerate).

    Returns
    -------
    HTMLResponse
        Updated PAT page.
    """
    user_id = await _get_session_user_id(request, db)
    if user_id is None:
        return RedirectResponse(url="/ui/login?next=/ui/settings/pats", status_code=302)

    svc = PATService(db)
    new_token = None
    error = None
    success = None

    if action == "create":
        if not name:
            error = "Token name is required."
        else:
            exp = None
            if expires_at:
                try:
                    exp = datetime.fromisoformat(expires_at).replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    error = "Invalid expiration date."

            if error is None:
                result = await svc.create(
                    user_id=user_id,
                    name=name,
                    scopes=scopes,
                    expires_at=exp,
                )
                new_token = result.token
                success = "Token created successfully."

    elif action == "regenerate":
        try:
            result = await svc.regenerate(uuid.UUID(pat_id), user_id)
            new_token = result.token
            success = "Token regenerated successfully."
        except (PATError, ValueError) as exc:
            error = str(exc)

    elif action == "revoke_all":
        count = await svc.revoke_all_for_user(user_id)
        success = f"All tokens revoked ({count})."

    elif action == "revoke":
        try:
            await svc.revoke(uuid.UUID(pat_id), user_id)
            success = "Token revoked."
        except (PATError, ValueError) as exc:
            error = str(exc)

    # Re-fetch token list
    pats = await svc.list_for_user(user_id)
    tokens = [
        {
            "id": str(p.id),
            "name": p.name,
            "token_prefix": p.token_prefix,
            "scopes": p.scopes,
            "expires_at": p.expires_at.isoformat() if p.expires_at else None,
            "last_used_at": p.last_used_at.isoformat() if p.last_used_at else None,
            "last_used_ip": p.last_used_ip,
            "use_count": p.use_count,
            "is_revoked": p.is_revoked,
        }
        for p in pats
    ]

    return _render(
        request,
        "settings/pats.html",
        {
            "tokens": tokens,
            "new_token": new_token,
            "error": error,
            "success": success,
        },
    )

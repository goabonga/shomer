# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Device code verification UI page per RFC 8628.

Users visit this page to enter (or auto-fill) a user_code and
approve or deny the device authorization request.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from shomer.deps import DbSession
from shomer.services.device_auth_service import DeviceAuthError, DeviceAuthService
from shomer.services.session_service import SessionService

router = APIRouter(prefix="/ui", tags=["ui"], include_in_schema=False)


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


@router.get("/device", response_class=HTMLResponse)
async def device_verify_page(
    request: Request, db: DbSession, user_code: str = ""
) -> Any:
    """Render the device code verification page.

    If ``user_code`` is provided (via verification_uri_complete),
    it is auto-filled in the form.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.
    user_code : str
        Pre-filled user code (from verification_uri_complete).

    Returns
    -------
    HTMLResponse
        Device verification page or redirect to login.
    """
    user_id = await _get_session_user_id(request, db)
    if user_id is None:
        from urllib.parse import quote

        next_url = (
            f"/ui/device?user_code={quote(user_code)}" if user_code else "/ui/device"
        )
        return RedirectResponse(
            url=f"/ui/login?next={quote(next_url)}", status_code=302
        )

    return _render(
        request,
        "device/verify.html",
        {
            "user_code": user_code,
        },
    )


@router.post("/device", response_class=HTMLResponse)
async def device_verify_submit(
    request: Request,
    db: DbSession,
    user_code: str = Form(...),
    action: str = Form(...),
) -> Any:
    """Handle device code verification form submission.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.
    user_code : str
        The user-entered verification code.
    action : str
        ``approve`` or ``deny``.

    Returns
    -------
    HTMLResponse
        Success or error page.
    """
    user_id = await _get_session_user_id(request, db)
    if user_id is None:
        return RedirectResponse(url="/ui/login?next=/ui/device", status_code=302)

    svc = DeviceAuthService(db)

    try:
        if action == "approve":
            await svc.approve(user_code=user_code, user_id=user_id)
            return _render(
                request,
                "device/verify.html",
                {
                    "success": "Device authorized successfully! You can close this page.",
                },
            )
        else:
            await svc.deny(user_code=user_code)
            return _render(
                request,
                "device/verify.html",
                {
                    "success": "Device authorization denied.",
                },
            )
    except DeviceAuthError as exc:
        return _render(
            request,
            "device/verify.html",
            {
                "user_code": user_code,
                "error": exc.description,
            },
        )

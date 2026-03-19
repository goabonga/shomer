# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Browser-facing password management UI routes (Jinja2/HTMX)."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from shomer.deps import DbSession
from shomer.services.auth_service import (
    AuthService,
    InvalidCredentialsError,
    InvalidResetTokenError,
)
from shomer.services.session_service import SessionService
from shomer.tasks.email import send_email_task

router = APIRouter(prefix="/ui", tags=["ui"], include_in_schema=False)


def _templates() -> Jinja2Templates:
    from shomer.app import templates

    return templates


def _render(request: Request, template: str, ctx: dict[str, Any] | None = None) -> Any:
    return _templates().TemplateResponse(request, template, ctx or {})


@router.get("/password/reset", response_class=HTMLResponse)
async def forgot_password_page(request: Request) -> Any:
    """Render the forgot password page."""
    return _render(request, "auth/forgot_password.html")


@router.post("/password/reset", response_class=HTMLResponse)
async def forgot_password_submit(
    request: Request, db: DbSession, email: str = Form(...)
) -> Any:
    """Handle forgot password form submission."""
    svc = AuthService(db)
    token = await svc.request_password_reset(email=email)

    # Always dispatch to prevent enumeration
    send_email_task.delay(
        to=email,
        subject="Reset your password",
        template="password_reset.html",
        context={"token": str(token) if token else ""},
    )

    return _render(
        request,
        "auth/forgot_password.html",
        {"success": "If the email is registered, a reset link has been sent."},
    )


@router.get("/password/reset-verify", response_class=HTMLResponse)
async def reset_password_page(request: Request, token: str = "") -> Any:
    """Render the reset password page."""
    return _render(request, "auth/reset_password.html", {"token": token})


@router.post("/password/reset-verify", response_class=HTMLResponse)
async def reset_password_submit(
    request: Request,
    db: DbSession,
    token: str = Form(...),
    new_password: str = Form(...),
) -> Any:
    """Handle reset password form submission."""
    svc = AuthService(db)
    try:
        token_uuid = uuid.UUID(token)
    except ValueError:
        return _render(
            request,
            "auth/reset_password.html",
            {"error": "Invalid reset token", "token": token},
        )

    try:
        await svc.verify_password_reset(token=token_uuid, new_password=new_password)
    except InvalidResetTokenError:
        return _render(
            request,
            "auth/reset_password.html",
            {"error": "Invalid or expired reset token", "token": token},
        )

    return _render(
        request,
        "auth/reset_password.html",
        {"success": "Password reset successfully. You can now log in."},
    )


@router.get("/password/change", response_class=HTMLResponse)
async def change_password_page(request: Request) -> Any:
    """Render the password change page."""
    return _render(request, "auth/change_password.html")


@router.post("/password/change", response_class=HTMLResponse)
async def change_password_submit(
    request: Request,
    db: DbSession,
    current_password: str = Form(...),
    new_password: str = Form(...),
) -> Any:
    """Handle password change form submission."""
    session_token = request.cookies.get("session_id")
    if not session_token:
        return _render(
            request, "auth/change_password.html", {"error": "Authentication required"}
        )

    svc_session = SessionService(db)
    session = await svc_session.validate(session_token)
    if session is None:
        return _render(
            request, "auth/change_password.html", {"error": "Session expired"}
        )

    svc = AuthService(db)
    try:
        await svc.change_password(
            user_id=session.user_id,
            current_password=current_password,
            new_password=new_password,
        )
    except InvalidCredentialsError:
        return _render(
            request,
            "auth/change_password.html",
            {"error": "Current password is incorrect"},
        )

    return _render(
        request,
        "auth/change_password.html",
        {"success": "Password changed successfully"},
    )

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Browser-facing authentication UI routes (Jinja2/HTMX)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from shomer.deps import DbSession
from shomer.services.auth_service import (
    AuthService,
    EmailNotFoundError,
    EmailNotVerifiedError,
    InvalidCodeError,
    InvalidCredentialsError,
    RateLimitError,
)
from shomer.tasks.email import send_email_task

router = APIRouter(prefix="/ui", tags=["ui"], include_in_schema=False)


def _templates() -> Jinja2Templates:
    from shomer.app import templates

    return templates


def _render(request: Request, template: str, ctx: dict[str, Any] | None = None) -> Any:
    return _templates().TemplateResponse(request, template, ctx or {})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request) -> Any:
    """Render the registration page."""
    return _render(request, "auth/register.html", {})


@router.post("/register", response_class=HTMLResponse)
async def register_submit(
    request: Request,
    db: DbSession,
    email: str = Form(...),
    password: str = Form(...),
    username: str = Form(""),
) -> Any:
    """Handle registration form submission.

    Always redirects to verify page to prevent user enumeration.
    """
    svc = AuthService(db)
    _, code = await svc.register(
        email=email,
        password=password,
        username=username or None,
    )

    # Always dispatch to equalize timing
    send_email_task.delay(
        to=email,
        subject="Verify your email",
        template="verification.html",
        context={"code": code},
    )

    return _render(
        request,
        "auth/verify.html",
        {"email": email, "success": "Check your email for a verification code."},
    )


@router.get("/verify", response_class=HTMLResponse)
async def verify_page(request: Request, email: str = "") -> Any:
    """Render the verification page."""
    return _render(request, "auth/verify.html", {"email": email})


@router.post("/verify", response_class=HTMLResponse)
async def verify_submit(
    request: Request,
    db: DbSession,
    email: str = Form(...),
    code: str = Form(...),
) -> Any:
    """Handle verification form submission."""
    svc = AuthService(db)
    try:
        await svc.verify_email(email=email, code=code)
    except InvalidCodeError:
        return _render(
            request,
            "auth/verify.html",
            {"email": email, "error": "Invalid or expired code"},
        )

    return _render(
        request, "auth/login.html", {"success": "Email verified! You can now log in."}
    )


@router.post("/verify/resend", response_class=HTMLResponse)
async def verify_resend(
    request: Request,
    db: DbSession,
    email: str = Form(...),
) -> Any:
    """Handle resend code form submission."""
    svc = AuthService(db)
    try:
        code = await svc.resend_code(email=email)
    except EmailNotFoundError:
        return _render(
            request, "auth/verify.html", {"email": email, "error": "Email not found"}
        )
    except RateLimitError:
        return _render(
            request,
            "auth/verify.html",
            {"email": email, "error": "Please wait before requesting a new code"},
        )

    send_email_task.delay(
        to=email,
        subject="Verify your email",
        template="verification.html",
        context={"code": code},
    )

    return _render(
        request, "auth/verify.html", {"email": email, "success": "New code sent!"}
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, next: str = "") -> Any:
    """Render the login page."""
    return _render(request, "auth/login.html", {"next": next})


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    db: DbSession,
    email: str = Form(...),
    password: str = Form(...),
    next: str = "",
) -> Any:
    """Handle login form submission."""
    from shomer.core.settings import get_settings
    from shomer.middleware.cookies import get_cookie_policy

    svc = AuthService(db)
    try:
        user, session = await svc.login(
            email=email,
            password=password,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
        )
    except InvalidCredentialsError:
        return _render(
            request,
            "auth/login.html",
            {"error": "Invalid email or password", "next": next},
        )
    except EmailNotVerifiedError:
        return _render(
            request, "auth/login.html", {"error": "Email not verified", "next": next}
        )

    redirect_url = next or "/"
    response = RedirectResponse(url=redirect_url, status_code=303)

    settings = get_settings()
    policy = get_cookie_policy(settings)
    response.set_cookie(
        key="session_id",
        value=session.token_hash,
        httponly=policy.httponly,
        secure=policy.secure,
        samesite=policy.samesite,
        domain=policy.domain or None,
        max_age=86400,
    )
    response.set_cookie(
        key="csrf_token",
        value=session.csrf_token,
        httponly=False,
        secure=policy.secure,
        samesite=policy.samesite,
        domain=policy.domain or None,
        max_age=86400,
    )
    return response

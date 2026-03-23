# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Browser-facing MFA UI routes (Jinja2/HTMX).

MFA setup page (QR code, verification), MFA challenge page (TOTP/email/backup
during login), and email fallback.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from shomer.deps import Config, DbSession
from shomer.services.mfa_service import MFAService
from shomer.services.session_service import SessionService

router = APIRouter(prefix="/ui/mfa", tags=["ui"], include_in_schema=False)


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


# ── MFA Setup ─────────────────────────────────────────────────────────


@router.get("/setup", response_class=HTMLResponse)
async def mfa_setup_page(request: Request, db: DbSession) -> Any:
    """Render the MFA setup page.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.

    Returns
    -------
    HTMLResponse
        MFA setup page or redirect to login.
    """
    user_id = await _get_session_user_id(request, db)
    if user_id is None:
        return RedirectResponse(url="/ui/login?next=/ui/mfa/setup", status_code=302)

    return _render(request, "mfa/setup.html")


@router.post("/setup", response_class=HTMLResponse)
async def mfa_setup_submit(
    request: Request,
    db: DbSession,
    config: Config,
    step: str = Form("generate"),
    code: str = Form(""),
) -> Any:
    """Handle MFA setup form submissions.

    Two steps: ``generate`` creates the TOTP secret, ``verify`` validates
    the code and enables MFA.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.
    config : Config
        Application settings.
    step : str
        ``generate`` or ``verify``.
    code : str
        TOTP code for verification step.

    Returns
    -------
    HTMLResponse
        Setup page with QR or backup codes.
    """
    user_id = await _get_session_user_id(request, db)
    if user_id is None:
        return RedirectResponse(url="/ui/login?next=/ui/mfa/setup", status_code=302)

    svc = MFAService(db, config)

    if step == "generate":
        # Generate TOTP secret
        from sqlalchemy import select

        from shomer.models.user_email import UserEmail
        from shomer.models.user_mfa import UserMFA

        secret = MFAService.generate_totp_secret()
        encrypted = svc.encrypt_totp_secret(secret)

        # Get email for provisioning URI
        email_stmt = select(UserEmail).where(
            UserEmail.user_id == user_id,
            UserEmail.is_primary == True,  # noqa: E712
        )
        email_result = await db.execute(email_stmt)
        primary = email_result.scalar_one_or_none()
        email = primary.email if primary else str(user_id)

        provisioning_uri = MFAService.get_provisioning_uri(
            secret, email=email, issuer="Shomer"
        )

        # Create or update UserMFA
        mfa_stmt = select(UserMFA).where(UserMFA.user_id == user_id)
        mfa_result = await db.execute(mfa_stmt)
        mfa = mfa_result.scalar_one_or_none()
        if mfa is None:
            mfa = UserMFA(
                user_id=user_id,
                totp_secret_encrypted=encrypted,
                is_enabled=False,
                methods=[],
            )
            db.add(mfa)
        else:
            mfa.totp_secret_encrypted = encrypted
        await db.flush()

        qr_code = MFAService.generate_qr_code_base64(provisioning_uri)

        return _render(
            request,
            "mfa/setup.html",
            {
                "secret": secret,
                "provisioning_uri": provisioning_uri,
                "qr_code": qr_code,
            },
        )

    # step == "verify"
    from sqlalchemy import select

    from shomer.models.user_mfa import UserMFA

    mfa_stmt = select(UserMFA).where(UserMFA.user_id == user_id)
    mfa_result = await db.execute(mfa_stmt)
    mfa = mfa_result.scalar_one_or_none()

    if mfa is None or not mfa.totp_secret_encrypted:
        return _render(request, "mfa/setup.html", {"error": "Please set up MFA first."})

    secret = svc.decrypt_totp_secret(mfa.totp_secret_encrypted)
    if not MFAService.verify_totp_code(secret, code):
        provisioning_uri = MFAService.get_provisioning_uri(
            secret, email=str(user_id), issuer="Shomer"
        )
        return _render(
            request,
            "mfa/setup.html",
            {
                "secret": secret,
                "provisioning_uri": provisioning_uri,
                "error": "Invalid code. Please try again.",
            },
        )

    # Enable MFA
    mfa.is_enabled = True
    mfa.methods = ["totp", "backup"]
    raw_codes = MFAService.generate_backup_codes()
    await svc.store_backup_codes(mfa.id, raw_codes)
    await db.flush()

    return _render(
        request,
        "mfa/setup.html",
        {"backup_codes": raw_codes, "success": "MFA enabled successfully!"},
    )


# ── MFA Challenge (during login) ─────────────────────────────────────


@router.get("/challenge", response_class=HTMLResponse)
async def mfa_challenge_page(
    request: Request,
    mfa_token: str = "",
    method: str = "totp",
) -> Any:
    """Render the MFA challenge page during login.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    mfa_token : str
        The MFA challenge JWT from the login response.
    method : str
        Verification method: ``totp``, ``email``, or ``backup``.

    Returns
    -------
    HTMLResponse
        MFA challenge page.
    """
    if not mfa_token:
        return RedirectResponse(url="/ui/login", status_code=302)

    # If switching to email, trigger email send
    if method == "email":
        from shomer.core.settings import get_settings
        from shomer.routes.auth import verify_mfa_token

        user_id_str = verify_mfa_token(mfa_token, get_settings())
        if user_id_str:
            # We don't send email here — user clicks a separate button or
            # the page loads with a message to send
            pass

    return _render(
        request,
        "mfa/challenge.html",
        {"mfa_token": mfa_token, "method": method},
    )


@router.post("/challenge", response_class=HTMLResponse)
async def mfa_challenge_submit(
    request: Request,
    db: DbSession,
    config: Config,
    mfa_token: str = Form(""),
    code: str = Form(""),
    method: str = Form("totp"),
) -> Any:
    """Handle MFA challenge form submission during login.

    Verifies the MFA code, creates a session, and redirects to home.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Database session.
    config : Config
        Application settings.
    mfa_token : str
        The MFA challenge JWT.
    code : str
        The verification code.
    method : str
        Verification method.

    Returns
    -------
    HTMLResponse or RedirectResponse
        Redirect to home on success, error page on failure.
    """
    from shomer.routes.auth import verify_mfa_token

    user_id_str = verify_mfa_token(mfa_token, config)
    if user_id_str is None:
        return _render(
            request,
            "mfa/challenge.html",
            {"error": "MFA session expired. Please login again.", "mfa_token": ""},
        )

    import uuid

    from sqlalchemy import select

    from shomer.models.user_mfa import UserMFA

    user_id = uuid.UUID(user_id_str)
    mfa_stmt = select(UserMFA).where(UserMFA.user_id == user_id)
    mfa_result = await db.execute(mfa_stmt)
    mfa = mfa_result.scalar_one_or_none()

    if mfa is None or not mfa.is_enabled:
        return _render(
            request,
            "mfa/challenge.html",
            {"error": "MFA is not enabled.", "mfa_token": mfa_token, "method": method},
        )

    svc = MFAService(db, config)
    valid = False

    if method == "backup":
        valid = await svc.verify_backup_code(mfa.id, code)
    elif method == "email":
        valid = await svc.verify_email_code(user_id=user_id, code=code)
    else:
        secret = svc.decrypt_totp_secret(mfa.totp_secret_encrypted or "")
        valid = MFAService.verify_totp_code(secret, code)

    if not valid:
        return _render(
            request,
            "mfa/challenge.html",
            {
                "error": "Invalid code. Please try again.",
                "mfa_token": mfa_token,
                "method": method,
            },
        )

    # MFA verified — create session
    from shomer.middleware.cookies import get_cookie_policy

    session_svc = SessionService(db)
    session, raw_token = await session_svc.create(
        user_id=user_id,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    await db.flush()

    policy = get_cookie_policy(config)
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(
        key="session_id",
        value=raw_token,
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

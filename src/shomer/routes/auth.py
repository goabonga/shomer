# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Authentication routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse

from shomer.deps import DbSession
from shomer.middleware.cookies import get_cookie_policy
from shomer.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    MessageResponse,
    PasswordChangeRequest,
    PasswordResetRequest,
    PasswordResetVerifyRequest,
    RegisterRequest,
    RegisterResponse,
    ResendRequest,
    VerifyRequest,
)
from shomer.services.auth_service import (
    AuthService,
    EmailNotFoundError,
    EmailNotVerifiedError,
    InvalidCodeError,
    InvalidCredentialsError,
    InvalidResetTokenError,
    RateLimitError,
)
from shomer.services.session_service import SessionService
from shomer.tasks.email import send_email_task

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(body: RegisterRequest, db: DbSession) -> RegisterResponse:
    """Register a new user account.

    Always returns 201 to prevent user enumeration. If the email
    already exists, a dummy hash is performed and the same success
    message is returned.

    Parameters
    ----------
    body : RegisterRequest
        Email, password, and optional username.
    db : DbSession
        Injected async database session.

    Returns
    -------
    RegisterResponse
        Confirmation message (always success).
    """
    svc = AuthService(db)
    user, code = await svc.register(
        email=body.email,
        password=body.password,
        username=body.username,
    )

    # Always dispatch a task to equalize timing
    send_email_task.delay(
        to=body.email,
        subject="Verify your email",
        template="verification.html",
        context={"code": code},
    )

    return RegisterResponse(
        message="Registration successful. Check your email for a verification code.",
        user_id=str(user.id) if user else "",
    )


@router.post("/verify", response_model=MessageResponse)
async def verify(body: VerifyRequest, db: DbSession) -> MessageResponse:
    """Verify an email address with a 6-digit code.

    Parameters
    ----------
    body : VerifyRequest
        Email and verification code.
    db : DbSession
        Injected async database session.

    Returns
    -------
    MessageResponse
        Success confirmation.

    Raises
    ------
    HTTPException
        400 if the code is invalid or expired.
    """
    svc = AuthService(db)
    try:
        await svc.verify_email(email=body.email, code=body.code)
    except InvalidCodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code",
        )
    return MessageResponse(message="Email verified successfully")


@router.post("/verify/resend", response_model=MessageResponse)
async def resend(body: ResendRequest, db: DbSession) -> MessageResponse:
    """Resend a verification code.

    Parameters
    ----------
    body : ResendRequest
        Email address.
    db : DbSession
        Injected async database session.

    Returns
    -------
    MessageResponse
        Success confirmation.

    Raises
    ------
    HTTPException
        404 if the email is not registered, 429 if rate limited.
    """
    svc = AuthService(db)
    try:
        code = await svc.resend_code(email=body.email)
    except EmailNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found",
        )
    except RateLimitError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Please wait before requesting a new code",
        )

    send_email_task.delay(
        to=body.email,
        subject="Verify your email",
        template="verification.html",
        context={"code": code},
    )

    return MessageResponse(message="Verification code sent")


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, request: Request, db: DbSession) -> JSONResponse:
    """Authenticate a user and create a session.

    Sets a secure session cookie on success.

    Parameters
    ----------
    body : LoginRequest
        Email and password.
    request : Request
        FastAPI request (for client metadata).
    db : DbSession
        Injected async database session.

    Returns
    -------
    JSONResponse
        Login confirmation with session cookie.

    Raises
    ------
    HTTPException
        401 if credentials are invalid, 403 if email not verified.
    """
    from shomer.core.settings import get_settings

    svc = AuthService(db)
    try:
        user, session = await svc.login(
            email=body.email,
            password=body.password,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    except EmailNotVerifiedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified",
        )

    settings = get_settings()
    policy = get_cookie_policy(settings)
    response = JSONResponse(
        content=LoginResponse(
            message="Login successful",
            user_id=str(user.id),
        ).model_dump(),
    )
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


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request, db: DbSession, body: LogoutRequest | None = None
) -> JSONResponse:
    """Log out the current user.

    Deletes the current session (or all sessions if ``logout_all``
    is ``True``) and clears the session cookies.

    Parameters
    ----------
    request : Request
        Incoming request with session cookie.
    db : DbSession
        Injected async database session.
    body : LogoutRequest or None
        Optional body with ``logout_all`` flag.

    Returns
    -------
    JSONResponse
        Logout confirmation with cleared cookies.
    """
    session_token = request.cookies.get("session_id")
    svc = SessionService(db)

    if session_token:
        session = await svc.validate(session_token)
        if session is not None:
            logout_all = body.logout_all if body else False
            if logout_all:
                await svc.delete_all_for_user(session.user_id)
            else:
                await svc.delete(session.id)

    response = JSONResponse(
        content=MessageResponse(message="Logged out successfully").model_dump(),
    )
    response.delete_cookie("session_id")
    response.delete_cookie("csrf_token")
    return response


@router.post("/password/reset", response_model=MessageResponse)
async def password_reset(body: PasswordResetRequest, db: DbSession) -> MessageResponse:
    """Request a password reset email.

    Always returns success to prevent user enumeration.

    Parameters
    ----------
    body : PasswordResetRequest
        Email address.
    db : DbSession
        Injected async database session.

    Returns
    -------
    MessageResponse
        Confirmation (always success).
    """
    svc = AuthService(db)
    token = await svc.request_password_reset(email=body.email)

    # Always dispatch a task to equalize timing. The email service
    # will silently discard sends to unregistered addresses, but the
    # Celery enqueue cost is constant either way.
    send_email_task.delay(
        to=body.email,
        subject="Reset your password",
        template="password_reset.html",
        context={"token": str(token) if token else ""},
    )

    return MessageResponse(
        message="If the email is registered, a reset link has been sent."
    )


@router.post("/password/reset-verify", response_model=MessageResponse)
async def password_reset_verify(
    body: PasswordResetVerifyRequest, db: DbSession
) -> MessageResponse:
    """Verify a reset token and set a new password.

    Parameters
    ----------
    body : PasswordResetVerifyRequest
        Reset token and new password.
    db : DbSession
        Injected async database session.

    Returns
    -------
    MessageResponse
        Confirmation of password change.

    Raises
    ------
    HTTPException
        400 if the token is invalid or expired.
    """
    import uuid as _uuid

    svc = AuthService(db)
    try:
        token_uuid = _uuid.UUID(body.token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )

    try:
        await svc.verify_password_reset(
            token=token_uuid, new_password=body.new_password
        )
    except InvalidResetTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    return MessageResponse(message="Password reset successfully")


@router.post("/password/change", response_model=MessageResponse)
async def password_change(
    body: PasswordChangeRequest, request: Request, db: DbSession
) -> MessageResponse:
    """Change the authenticated user's password.

    Requires a valid session cookie.

    Parameters
    ----------
    body : PasswordChangeRequest
        Current and new passwords.
    request : Request
        Incoming request with session cookie.
    db : DbSession
        Injected async database session.

    Returns
    -------
    MessageResponse
        Confirmation of password change.

    Raises
    ------
    HTTPException
        401 if not authenticated or current password is wrong.
    """
    session_token = request.cookies.get("session_id")
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    svc_session = SessionService(db)
    session = await svc_session.validate(session_token)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    svc = AuthService(db)
    try:
        await svc.change_password(
            user_id=session.user_id,
            current_password=body.current_password,
            new_password=body.new_password,
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )

    return MessageResponse(message="Password changed successfully")

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
    RegisterRequest,
    RegisterResponse,
    ResendRequest,
    VerifyRequest,
)
from shomer.services.auth_service import (
    AuthService,
    DuplicateEmailError,
    EmailNotFoundError,
    EmailNotVerifiedError,
    InvalidCodeError,
    InvalidCredentialsError,
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

    Creates the user with hashed password, generates a verification code,
    and dispatches a verification email via Celery.

    Parameters
    ----------
    body : RegisterRequest
        Email, password, and optional username.
    db : DbSession
        Injected async database session.

    Returns
    -------
    RegisterResponse
        Confirmation with user ID.

    Raises
    ------
    HTTPException
        409 if the email is already registered.
    """
    svc = AuthService(db)
    try:
        user, code = await svc.register(
            email=body.email,
            password=body.password,
            username=body.username,
        )
    except DuplicateEmailError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Dispatch verification email asynchronously
    send_email_task.delay(
        to=body.email,
        subject="Verify your email",
        template="verification.html",
        context={"code": code},
    )

    return RegisterResponse(
        message="Registration successful. Check your email for a verification code.",
        user_id=str(user.id),
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

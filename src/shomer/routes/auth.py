# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Authentication routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from shomer.deps import DbSession
from shomer.schemas.auth import (
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
    InvalidCodeError,
    RateLimitError,
)
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

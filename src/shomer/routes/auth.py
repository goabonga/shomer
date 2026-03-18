# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Authentication routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from shomer.deps import DbSession
from shomer.schemas.auth import RegisterRequest, RegisterResponse
from shomer.services.auth_service import AuthService, DuplicateEmailError
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

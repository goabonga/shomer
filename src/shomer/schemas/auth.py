# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Request and response schemas for authentication endpoints."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Registration request body.

    Attributes
    ----------
    email : str
        User email address.
    password : str
        Plain-text password (min 8 characters).
    username : str or None
        Optional display name.
    """

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    username: str | None = Field(default=None, max_length=255)


class VerifyRequest(BaseModel):
    """Email verification request body.

    Attributes
    ----------
    email : str
        Email address to verify.
    code : str
        Six-digit verification code.
    """

    email: EmailStr
    code: str = Field(min_length=6, max_length=6)


class ResendRequest(BaseModel):
    """Resend verification code request body.

    Attributes
    ----------
    email : str
        Email address to resend the code to.
    """

    email: EmailStr


class MessageResponse(BaseModel):
    """Generic message response.

    Attributes
    ----------
    message : str
        Human-readable message.
    """

    message: str


class RegisterResponse(BaseModel):
    """Registration success response.

    Attributes
    ----------
    message : str
        Confirmation message.
    user_id : str
        Created user's UUID.
    """

    message: str
    user_id: str

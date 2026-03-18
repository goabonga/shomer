# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Basic CRUD query helpers for user models."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shomer.models.user import User
from shomer.models.user_email import UserEmail
from shomer.models.user_password import UserPassword


async def create_user(
    session: AsyncSession,
    *,
    email: str,
    password_hash: str,
    username: str | None = None,
) -> User:
    """Create a user with a primary email and password.

    Parameters
    ----------
    session : AsyncSession
        Database session.
    email : str
        Primary email address.
    password_hash : str
        Argon2id hashed password.
    username : str or None
        Optional display name.

    Returns
    -------
    User
        The newly created user.
    """
    user = User(username=username)
    session.add(user)
    await session.flush()

    user_email = UserEmail(
        user_id=user.id,
        email=email,
        is_primary=True,
    )
    user_password = UserPassword(
        user_id=user.id,
        password_hash=password_hash,
    )
    session.add_all([user_email, user_password])
    await session.flush()
    return user


async def get_user_by_id(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> User | None:
    """Fetch a user by ID with emails and passwords eagerly loaded.

    Parameters
    ----------
    session : AsyncSession
        Database session.
    user_id : uuid.UUID
        User primary key.

    Returns
    -------
    User or None
        The user if found.
    """
    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.emails), selectinload(User.passwords))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_email(
    session: AsyncSession,
    email: str,
) -> User | None:
    """Fetch a user by email address.

    Parameters
    ----------
    session : AsyncSession
        Database session.
    email : str
        Email address to look up.

    Returns
    -------
    User or None
        The user if found.
    """
    stmt = (
        select(User)
        .join(UserEmail)
        .where(UserEmail.email == email)
        .options(selectinload(User.emails), selectinload(User.passwords))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

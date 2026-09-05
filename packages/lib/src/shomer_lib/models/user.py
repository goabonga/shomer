# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""The authenticated subject."""

from __future__ import annotations

from sqlalchemy import Boolean, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from shomer_lib.models.base import Base


class User(Base):
    """A person Shomer can authenticate.

    `subject` is the stable identifier handed to relying parties as the
    `sub` claim. It is separate from the e-mail on purpose: an address can
    change hands, and a `sub` that changes with it silently reassigns
    every account that trusted it.
    """

    __tablename__ = "users"

    subject: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    # Never the password. Shomer stores a verifier; what algorithm
    # produced it is the credential layer's business, not this table's.
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[float] = mapped_column(Float)

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""The relying party."""

from __future__ import annotations

from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shomer_lib.models.base import Base


class Client(Base):
    """An OAuth 2.0 client registered with this authorization server.

    `redirect_uris` is stored as a newline-separated list rather than a
    JSON blob: the values are compared for exact string equality on every
    authorization request, and a format the database can index and a human
    can read in a support ticket is worth more here than a structure
    nothing queries into.
    """

    __tablename__ = "clients"

    client_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    # Null for a public client (a browser or mobile app), which has no
    # place to keep a secret and proves itself with PKCE instead.
    client_secret_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    redirect_uris: Mapped[str] = mapped_column(Text)
    created_at: Mapped[float] = mapped_column(Float)

    def allows(self, redirect_uri: str) -> bool:
        """Whether `redirect_uri` is one of the registered values.

        Exact match, never a prefix or a suffix: a prefix match on
        `https://app.example.com/` also accepts
        `https://app.example.com.attacker.test/`, which is how an
        authorization code leaves for someone else's server.
        """
        return redirect_uri in self.redirect_uris.splitlines()

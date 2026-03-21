# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""PARRequest model for RFC 9126 Pushed Authorization Requests."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from shomer.core.database import Base, TimestampMixin, UUIDMixin


class PARRequest(Base, UUIDMixin, TimestampMixin):
    """Pushed Authorization Request per RFC 9126.

    Stores the authorization request parameters pushed by the client
    before redirecting the user. The ``request_uri`` is used by
    ``/authorize`` to retrieve the pre-validated parameters.

    Attributes
    ----------
    id : uuid.UUID
        Primary key (from UUIDMixin).
    request_uri : str
        Unique URI (``urn:ietf:params:oauth:request_uri:xxx``), indexed.
    client_id : str
        OAuth2 client that pushed the request.
    parameters : dict
        JSON object with all authorization request parameters
        (response_type, redirect_uri, scope, state, nonce, etc.).
    expires_at : datetime
        Expiration timestamp (default 60 seconds).
    created_at : datetime
        Row creation timestamp (from TimestampMixin).
    updated_at : datetime
        Last update timestamp (from TimestampMixin).
    """

    __tablename__ = "par_requests"

    request_uri: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    client_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    parameters: Mapped[dict] = mapped_column(  # type: ignore[type-arg]
        JSON,
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<PARRequest uri={self.request_uri[:40]}... client={self.client_id}>"

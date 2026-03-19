# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Sliding session expiration middleware."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from shomer.core.database import async_session
from shomer.services.session_service import SessionService


class SessionMiddleware(BaseHTTPMiddleware):
    """Renew active sessions on each authenticated request.

    Reads the ``session_id`` cookie, validates the session, and
    extends its TTL via the sliding window mechanism. Unauthenticated
    requests (no cookie or invalid session) are passed through unchanged.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process the request, renewing the session if present.

        Parameters
        ----------
        request : Request
            Incoming HTTP request.
        call_next : RequestResponseEndpoint
            Next middleware or route handler.

        Returns
        -------
        Response
            The response from downstream handlers.
        """
        session_token = request.cookies.get("session_id")
        if session_token:
            async with async_session() as db:
                svc = SessionService(db)
                session = await svc.validate(session_token)
                if session is not None:
                    await svc.renew(session)
                    await db.commit()

        return await call_next(request)

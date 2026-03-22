# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Tenant resolution middleware.

Resolves the current tenant from the request using three strategies
(in order): subdomain, path prefix, or custom domain lookup. Sets
the resolved tenant ID on ``request.state.tenant_id``.
"""

from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from shomer.core.database import async_session
from shomer.services.tenant_resolver_service import TenantResolverService


class TenantMiddleware(BaseHTTPMiddleware):
    """Resolve the current tenant for every request.

    Resolution strategies (tried in order):

    1. **Subdomain** — ``acme.shomer.io`` → slug ``acme``
    2. **Path prefix** — ``/t/acme/...`` → slug ``acme``
    3. **Custom domain** — ``auth.acme.com`` → domain lookup

    The resolved tenant ID is stored on ``request.state.tenant_id``.
    If no tenant is found, ``request.state.tenant_id`` is ``None``
    (fallback to default / global context).
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Resolve tenant and continue request processing.

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
        tenant_id: uuid.UUID | None = None

        async with async_session() as db:
            svc = TenantResolverService(db)
            tenant_id = await svc.resolve(request)

        request.state.tenant_id = tenant_id
        return await call_next(request)

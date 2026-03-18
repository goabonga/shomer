# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""CORS middleware with dynamic per-tenant origin resolution."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shomer.core.settings import Settings

#: Origins allowed in development mode.
DEV_ORIGINS: list[str] = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
]


def resolve_origins(
    settings: Settings, tenant_origins: list[str] | None = None
) -> list[str]:
    """Build the list of allowed CORS origins.

    Merges configured origins, optional per-tenant origins, and
    development-mode localhost origins.

    Parameters
    ----------
    settings : Settings
        Application settings.
    tenant_origins : list[str] or None
        Additional origins for a specific tenant.

    Returns
    -------
    list[str]
        Deduplicated list of allowed origins.
    """
    origins: list[str] = list(settings.cors_allowed_origins)

    if tenant_origins:
        origins.extend(tenant_origins)

    if settings.debug:
        origins.extend(DEV_ORIGINS)

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for origin in origins:
        if origin not in seen:
            seen.add(origin)
            unique.append(origin)
    return unique


def setup_cors(app: FastAPI, settings: Settings) -> None:
    """Add CORS middleware to the FastAPI application.

    Parameters
    ----------
    app : FastAPI
        The application instance.
    settings : Settings
        Application settings providing CORS configuration.
    """
    origins = resolve_origins(settings)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allowed_methods,
        allow_headers=settings.cors_allowed_headers,
    )

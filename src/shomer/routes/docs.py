# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Documentation routes."""

from fastapi import APIRouter, Request
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import HTMLResponse

router = APIRouter()

FAVICON_URL = "/static/favicon.ico"


@router.get("/docs", include_in_schema=False)
def docs(request: Request) -> HTMLResponse:
    """Render the Swagger UI documentation."""
    return get_swagger_ui_html(
        openapi_url=request.app.openapi_url,
        title=f"{request.app.title} - Docs",
        swagger_favicon_url=FAVICON_URL,
    )


@router.get("/redoc", include_in_schema=False)
def redoc(request: Request) -> HTMLResponse:
    """Render the ReDoc documentation."""
    return get_redoc_html(
        openapi_url=request.app.openapi_url,
        title=f"{request.app.title} - ReDoc",
        redoc_favicon_url=FAVICON_URL,
    )

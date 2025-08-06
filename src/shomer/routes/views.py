# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""HTML view routes."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from shomer import __version__

router = APIRouter()


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def index(request: Request) -> HTMLResponse:
    """Render the home page."""
    from shomer.app import templates

    return templates.TemplateResponse(request, "index.html", {"version": __version__})

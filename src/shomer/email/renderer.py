# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Jinja2 template rendering engine for email bodies.

Supports tenant branding injection (logo, colors, app name).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

#: Default directory for email templates.
_TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "email"

#: Default branding values used when no tenant branding is provided.
DEFAULT_BRANDING: dict[str, str] = {
    "app_name": "Shomer",
    "primary_color": "#1a1a2e",
    "secondary_color": "#16213e",
    "bg_color": "#f4f4f7",
}


def create_env(template_dir: Path | None = None) -> Environment:
    """Create a Jinja2 environment for email templates.

    Parameters
    ----------
    template_dir : Path or None
        Directory containing the templates.  Defaults to
        ``src/shomer/templates/email/``.

    Returns
    -------
    Environment
        Configured Jinja2 environment.
    """
    directory = template_dir or _TEMPLATE_DIR
    return Environment(
        loader=FileSystemLoader(str(directory)),
        autoescape=select_autoescape(["html", "xml"]),
    )


def render_template(
    template_name: str,
    context: dict[str, object],
    *,
    template_dir: Path | None = None,
    branding: dict[str, Any] | None = None,
) -> str:
    """Render an email template to a string with branding support.

    Injects default branding variables (``app_name``, ``primary_color``,
    etc.) which can be overridden by the ``branding`` parameter or
    individual ``context`` keys.

    Parameters
    ----------
    template_name : str
        Template file name (e.g. ``"verification.html"``).
    context : dict[str, object]
        Variables passed to the template.
    template_dir : Path or None
        Override template directory.
    branding : dict[str, Any] or None
        Tenant branding overrides (logo_url, primary_color, etc.).

    Returns
    -------
    str
        Rendered HTML string.
    """
    env = create_env(template_dir)
    template = env.get_template(template_name)

    # Build final context: defaults < branding < explicit context
    merged: dict[str, object] = {
        **DEFAULT_BRANDING,
        "year": str(datetime.now(timezone.utc).year),
    }
    if branding:
        merged.update(branding)
    merged.update(context)

    return template.render(merged)

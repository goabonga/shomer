# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Jinja2 template rendering engine for email bodies."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

#: Default directory for email templates.
_TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "email"


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
) -> str:
    """Render an email template to a string.

    Parameters
    ----------
    template_name : str
        Template file name (e.g. ``"verification.html"``).
    context : dict[str, object]
        Variables passed to the template.
    template_dir : Path or None
        Override template directory.

    Returns
    -------
    str
        Rendered HTML string.
    """
    env = create_env(template_dir)
    template = env.get_template(template_name)
    return template.render(context)

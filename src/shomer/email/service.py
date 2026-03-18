# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""High-level email service."""

from __future__ import annotations

from pathlib import Path

from shomer.core.settings import Settings
from shomer.email.backend import EmailBackend, SmtpBackend
from shomer.email.renderer import render_template


class EmailService:
    """Orchestrates template rendering and email dispatch.

    Attributes
    ----------
    backend : EmailBackend
        The delivery backend (SMTP by default).
    """

    def __init__(
        self,
        settings: Settings,
        *,
        backend: EmailBackend | None = None,
    ) -> None:
        self.settings = settings
        self.backend = backend or SmtpBackend(settings)

    def send_email(
        self,
        *,
        to: str,
        subject: str,
        template: str,
        context: dict[str, object] | None = None,
        template_dir: Path | None = None,
    ) -> None:
        """Render a template and send the resulting email.

        Parameters
        ----------
        to : str
            Recipient email address.
        subject : str
            Email subject line.
        template : str
            Template file name (e.g. ``"verification.html"``).
        context : dict[str, object] or None
            Variables passed to the template.
        template_dir : Path or None
            Override template directory.
        """
        html_body = render_template(template, context or {}, template_dir=template_dir)
        self.backend.send(to=to, subject=subject, html_body=html_body)

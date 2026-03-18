# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Celery tasks for asynchronous email dispatch."""

from __future__ import annotations

from typing import Any

from celery import Task

from shomer.core.settings import get_settings
from shomer.email.service import EmailService
from shomer.worker import app

#: Maximum number of retry attempts for transient SMTP failures.
MAX_RETRIES = 3

#: Backoff interval between retries (in seconds).
RETRY_BACKOFF = 60


@app.task(  # type: ignore[misc]
    bind=True,
    max_retries=MAX_RETRIES,
    default_retry_delay=RETRY_BACKOFF,
    autoretry_for=(OSError,),
    retry_backoff=True,
    retry_jitter=True,
)
def send_email_task(
    self: Task,  # noqa: ARG001
    *,
    to: str,
    subject: str,
    template: str,
    context: dict[str, Any] | None = None,
) -> None:
    """Send an email asynchronously via Celery.

    Retries up to ``MAX_RETRIES`` times with exponential backoff on
    transient network/SMTP errors (``OSError`` subclasses).

    Parameters
    ----------
    self : celery.Task
        Bound task instance (for retry support).
    to : str
        Recipient email address.
    subject : str
        Email subject line.
    template : str
        Template file name.
    context : dict[str, Any] or None
        Variables for template rendering.
    """
    settings = get_settings()
    service = EmailService(settings)
    service.send_email(
        to=to,
        subject=subject,
        template=template,
        context=context,
    )

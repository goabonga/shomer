# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Celery worker for the Shomer authentication service."""

from celery import Celery
from celery.schedules import crontab

from shomer.core.settings import get_settings

settings = get_settings()

app = Celery(
    "shomer",
    broker=settings.celery_broker_url,
    backend=settings.celery_backend,
)

app.config_from_object(
    {
        "task_serializer": "json",
        "result_serializer": "json",
        "accept_content": ["json"],
        "timezone": "UTC",
        "enable_utc": True,
        "beat_schedule": {
            "cleanup-access-tokens": {
                "task": "shomer.cleanup.access_tokens",
                "schedule": crontab(minute="*/15"),
            },
            "cleanup-refresh-tokens": {
                "task": "shomer.cleanup.refresh_tokens",
                "schedule": crontab(minute=0, hour="*/6"),
            },
            "cleanup-authorization-codes": {
                "task": "shomer.cleanup.authorization_codes",
                "schedule": crontab(minute="*/15"),
            },
            "cleanup-device-codes": {
                "task": "shomer.cleanup.device_codes",
                "schedule": crontab(minute=0, hour="*/6"),
            },
            "cleanup-par-requests": {
                "task": "shomer.cleanup.par_requests",
                "schedule": crontab(minute="*/15"),
            },
            "cleanup-verification-codes": {
                "task": "shomer.cleanup.verification_codes",
                "schedule": crontab(minute=0, hour="*/6"),
            },
            "cleanup-sessions": {
                "task": "shomer.cleanup.sessions",
                "schedule": crontab(minute=0, hour="*/1"),
            },
            "cleanup-mfa-codes": {
                "task": "shomer.cleanup.mfa_codes",
                "schedule": crontab(minute="*/15"),
            },
            "cleanup-revoked-pats": {
                "task": "shomer.cleanup.revoked_pats",
                "schedule": crontab(minute=0, hour=3),
            },
        },
        "include": ["shomer.tasks.email", "shomer.tasks.cleanup"],
    }
)

app.autodiscover_tasks(["shomer.tasks"])

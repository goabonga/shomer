# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Celery worker for the Shomer authentication service."""

from celery import Celery

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
        "beat_schedule": {},
    }
)

app.autodiscover_tasks(["shomer.tasks"])

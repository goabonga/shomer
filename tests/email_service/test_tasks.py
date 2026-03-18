# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for Celery email tasks."""

from shomer.tasks.email import MAX_RETRIES, RETRY_BACKOFF, send_email_task


class TestSendEmailTask:
    """Tests for send_email_task Celery task."""

    def test_task_is_registered(self) -> None:
        assert send_email_task.name is not None

    def test_max_retries_configured(self) -> None:
        assert send_email_task.max_retries == MAX_RETRIES

    def test_retry_backoff_configured(self) -> None:
        assert send_email_task.default_retry_delay == RETRY_BACKOFF

    def test_autoretry_for_os_error(self) -> None:
        assert OSError in send_email_task.autoretry_for

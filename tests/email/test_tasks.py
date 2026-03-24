# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for Celery email tasks."""

from unittest.mock import MagicMock, patch

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

    @patch("shomer.tasks.email.EmailService")
    def test_sends_email(self, mock_cls: MagicMock) -> None:
        """Task instantiates EmailService and calls send_email."""
        mock_svc = MagicMock()
        mock_cls.return_value = mock_svc

        send_email_task.run(
            to="test@example.com",
            subject="Hello",
            template="verification.html",
            context={"code": "123456"},
        )

        mock_cls.assert_called_once()
        mock_svc.send_email.assert_called_once_with(
            to="test@example.com",
            subject="Hello",
            template="verification.html",
            context={"code": "123456"},
        )

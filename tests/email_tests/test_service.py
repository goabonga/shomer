# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for EmailService."""

from pathlib import Path
from unittest.mock import MagicMock

from shomer.core.settings import Settings
from shomer.email.backend import EmailBackend
from shomer.email.service import EmailService


class TestEmailService:
    """Tests for EmailService.send_email()."""

    def test_renders_and_sends(self, tmp_path: Path) -> None:
        (tmp_path / "test.html").write_text("Hello {{ name }}!")

        mock_backend = MagicMock(spec=EmailBackend)
        service = EmailService(Settings(), backend=mock_backend)
        service.send_email(
            to="user@example.com",
            subject="Welcome",
            template="test.html",
            context={"name": "Bob"},
            template_dir=tmp_path,
        )

        mock_backend.send.assert_called_once_with(
            to="user@example.com",
            subject="Welcome",
            html_body="Hello Bob!",
        )

    def test_empty_context_defaults_to_empty_dict(self, tmp_path: Path) -> None:
        (tmp_path / "static.html").write_text("Static content")

        mock_backend = MagicMock(spec=EmailBackend)
        service = EmailService(Settings(), backend=mock_backend)
        service.send_email(
            to="a@b.com",
            subject="S",
            template="static.html",
            template_dir=tmp_path,
        )

        mock_backend.send.assert_called_once_with(
            to="a@b.com",
            subject="S",
            html_body="Static content",
        )

    def test_uses_smtp_backend_by_default(self) -> None:
        from shomer.email.backend import SmtpBackend

        service = EmailService(Settings())
        assert isinstance(service.backend, SmtpBackend)

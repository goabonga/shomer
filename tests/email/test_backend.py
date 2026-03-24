# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for email backends with mock SMTP server."""

import smtplib
from unittest.mock import MagicMock, patch

import pytest

from shomer.core.settings import Settings
from shomer.email.backend import EmailBackend, SmtpBackend


class TestEmailBackendInterface:
    """Tests for EmailBackend ABC."""

    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            EmailBackend(Settings())  # type: ignore[abstract]


class TestSmtpBackend:
    """Tests for SmtpBackend with mock SMTP."""

    def _settings(self, **kwargs: object) -> Settings:
        defaults = {
            "smtp_host": "mail.example.com",
            "smtp_port": 587,
            "smtp_user": "user",
            "smtp_password": "pass",
            "smtp_use_tls": True,
            "email_from_address": "noreply@example.com",
            "email_from_name": "Test",
        }
        defaults.update(kwargs)
        return Settings(**defaults)  # type: ignore[arg-type]

    @patch("shomer.email.backend.smtplib.SMTP")
    def test_sends_email(self, mock_smtp_cls: MagicMock) -> None:
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        backend = SmtpBackend(self._settings())
        backend.send(
            to="user@example.com",
            subject="Test",
            html_body="<p>Hello</p>",
        )

        mock_smtp_cls.assert_called_once_with("mail.example.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user", "pass")
        mock_server.sendmail.assert_called_once()

    @patch("shomer.email.backend.smtplib.SMTP")
    def test_no_tls_when_disabled(self, mock_smtp_cls: MagicMock) -> None:
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        backend = SmtpBackend(self._settings(smtp_use_tls=False))
        backend.send(to="a@b.com", subject="S", html_body="<p>X</p>")

        mock_server.starttls.assert_not_called()

    @patch("shomer.email.backend.smtplib.SMTP")
    def test_no_login_when_user_empty(self, mock_smtp_cls: MagicMock) -> None:
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        backend = SmtpBackend(self._settings(smtp_user=""))
        backend.send(to="a@b.com", subject="S", html_body="<p>X</p>")

        mock_server.login.assert_not_called()

    @patch("shomer.email.backend.smtplib.SMTP")
    def test_smtp_error_propagates(self, mock_smtp_cls: MagicMock) -> None:
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_server.sendmail.side_effect = smtplib.SMTPException("fail")

        backend = SmtpBackend(self._settings())
        with pytest.raises(smtplib.SMTPException, match="fail"):
            backend.send(to="a@b.com", subject="S", html_body="<p>X</p>")

    @patch("shomer.email.backend.smtplib.SMTP")
    def test_from_header_format(self, mock_smtp_cls: MagicMock) -> None:
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        backend = SmtpBackend(self._settings())
        backend.send(to="a@b.com", subject="S", html_body="<p>X</p>")

        sent_msg = mock_server.sendmail.call_args[0][2]
        assert "Test <noreply@example.com>" in sent_msg

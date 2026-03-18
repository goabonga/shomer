# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Email backend interface and SMTP implementation."""

from __future__ import annotations

import smtplib
from abc import ABC, abstractmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from shomer.core.settings import Settings


class EmailBackend(ABC):
    """Abstract base class for email backends.

    Attributes
    ----------
    settings : Settings
        Application configuration.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @abstractmethod
    def send(
        self,
        *,
        to: str,
        subject: str,
        html_body: str,
    ) -> None:
        """Send an email.

        Parameters
        ----------
        to : str
            Recipient email address.
        subject : str
            Email subject line.
        html_body : str
            Rendered HTML body.
        """


class SmtpBackend(EmailBackend):
    """SMTP email backend.

    Connects to the configured SMTP server and delivers messages
    using STARTTLS when enabled.
    """

    def send(
        self,
        *,
        to: str,
        subject: str,
        html_body: str,
    ) -> None:
        """Send an email via SMTP.

        Parameters
        ----------
        to : str
            Recipient email address.
        subject : str
            Email subject line.
        html_body : str
            Rendered HTML body.

        Raises
        ------
        smtplib.SMTPException
            If the SMTP server rejects the message.
        """
        msg = MIMEMultipart("alternative")
        msg["From"] = (
            f"{self.settings.email_from_name} <{self.settings.email_from_address}>"
        )
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as server:
            if self.settings.smtp_use_tls:
                server.starttls()
            if self.settings.smtp_user:
                server.login(self.settings.smtp_user, self.settings.smtp_password)
            server.sendmail(self.settings.email_from_address, [to], msg.as_string())

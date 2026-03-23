# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for production email templates with branding."""

from __future__ import annotations

from shomer.email.renderer import DEFAULT_BRANDING, render_template


class TestProductionTemplates:
    """Tests for MJML-derived email templates with branding."""

    def test_verification_renders_code(self) -> None:
        """Verification template renders the code."""
        html = render_template("verification.html", {"code": "123456"})
        assert "123456" in html
        assert "Verify your email" in html

    def test_password_reset_renders_link(self) -> None:
        """Password reset template renders the reset link."""
        html = render_template(
            "password_reset.html",
            {"token": "https://example.com/reset/abc"},
        )
        assert "Reset your password" in html
        assert "https://example.com/reset/abc" in html

    def test_mfa_code_renders(self) -> None:
        """MFA code template renders the code."""
        html = render_template("mfa_code.html", {"code": "654321"})
        assert "654321" in html
        assert "verification code" in html

    def test_welcome_renders_with_username(self) -> None:
        """Welcome template renders with username."""
        html = render_template("welcome.html", {"username": "Alice"})
        assert "Alice" in html
        assert "Welcome" in html

    def test_welcome_without_username(self) -> None:
        """Welcome template renders without username."""
        html = render_template("welcome.html", {})
        assert "Welcome" in html

    def test_welcome_with_login_url(self) -> None:
        """Welcome template renders login button."""
        html = render_template(
            "welcome.html", {"login_url": "https://example.com/login"}
        )
        assert "Go to Login" in html

    def test_default_branding_applied(self) -> None:
        """Default branding colors injected."""
        html = render_template("verification.html", {"code": "000000"})
        assert DEFAULT_BRANDING["primary_color"] in html
        assert "Shomer" in html

    def test_custom_branding_overrides(self) -> None:
        """Custom branding overrides defaults."""
        html = render_template(
            "verification.html",
            {"code": "000000"},
            branding={
                "app_name": "Acme Auth",
                "primary_color": "#ff0000",
                "logo_url": "https://acme.com/logo.png",
            },
        )
        assert "Acme Auth" in html
        assert "#ff0000" in html
        assert "https://acme.com/logo.png" in html

    def test_context_overrides_branding(self) -> None:
        """Explicit context takes precedence over branding."""
        html = render_template(
            "verification.html",
            {"code": "111111", "app_name": "Override"},
            branding={"app_name": "Branding"},
        )
        assert "Override" in html

    def test_year_injected(self) -> None:
        """Current year injected into footer."""
        from datetime import datetime, timezone

        html = render_template("verification.html", {"code": "000000"})
        assert str(datetime.now(timezone.utc).year) in html

    def test_responsive_meta(self) -> None:
        """Base template includes viewport meta."""
        html = render_template("verification.html", {"code": "000000"})
        assert "viewport" in html

    def test_support_url_in_footer(self) -> None:
        """Support link shown when provided."""
        html = render_template(
            "verification.html",
            {"code": "000000"},
            branding={"support_url": "https://help.example.com"},
        )
        assert "https://help.example.com" in html

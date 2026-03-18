# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for secure cookie policy."""

from shomer.core.settings import Settings
from shomer.middleware.cookies import CookiePolicy, get_cookie_policy


class TestCookiePolicy:
    """Tests for CookiePolicy dataclass."""

    def test_immutable(self) -> None:
        policy = CookiePolicy(secure=True, httponly=True, samesite="lax", domain="")
        assert policy.secure is True
        assert policy.httponly is True
        assert policy.samesite == "lax"
        assert policy.domain == ""

    def test_frozen(self) -> None:
        policy = CookiePolicy(secure=True, httponly=True, samesite="lax", domain="")
        try:
            policy.secure = False  # type: ignore[misc]
            raised = False
        except AttributeError:
            raised = True
        assert raised


class TestGetCookiePolicy:
    """Tests for get_cookie_policy()."""

    def test_production_defaults(self) -> None:
        settings = Settings(debug=False)
        policy = get_cookie_policy(settings)
        assert policy.secure is True
        assert policy.httponly is True
        assert policy.samesite == "lax"
        assert policy.domain == ""

    def test_debug_disables_secure(self) -> None:
        settings = Settings(debug=True)
        policy = get_cookie_policy(settings)
        assert policy.secure is False

    def test_httponly_always_on(self) -> None:
        settings = Settings(debug=True)
        policy = get_cookie_policy(settings)
        assert policy.httponly is True

    def test_custom_samesite(self) -> None:
        settings = Settings(cookie_samesite="strict")
        policy = get_cookie_policy(settings)
        assert policy.samesite == "strict"

    def test_custom_domain(self) -> None:
        settings = Settings(cookie_domain=".example.com")
        policy = get_cookie_policy(settings)
        assert policy.domain == ".example.com"

    def test_secure_explicit_false_stays_false(self) -> None:
        settings = Settings(cookie_secure=False, debug=False)
        policy = get_cookie_policy(settings)
        assert policy.secure is False

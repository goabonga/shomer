# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Secure cookie defaults."""

from __future__ import annotations

from dataclasses import dataclass

from shomer.core.settings import Settings


@dataclass(frozen=True)
class CookiePolicy:
    """Immutable secure cookie policy.

    Attributes
    ----------
    secure : bool
        Set the ``Secure`` flag.
    httponly : bool
        Set the ``HttpOnly`` flag.
    samesite : str
        ``SameSite`` attribute (``lax``, ``strict``, or ``none``).
    domain : str
        Cookie domain scope. Empty string means current domain only.
    """

    secure: bool
    httponly: bool
    samesite: str
    domain: str


def get_cookie_policy(settings: Settings) -> CookiePolicy:
    """Build a cookie policy from application settings.

    In debug mode, ``Secure`` is automatically disabled so cookies
    work over plain HTTP on localhost.

    Parameters
    ----------
    settings : Settings
        Application settings.

    Returns
    -------
    CookiePolicy
        The resolved cookie policy.
    """
    secure = settings.cookie_secure and not settings.debug
    return CookiePolicy(
        secure=secure,
        httponly=settings.cookie_httponly,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
    )

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""Behave hooks for the shomer-ssr end-to-end suite.

One Chromium instance for the whole run, and one page per scenario. The
browser is what makes this suite worth its cost: it exercises the bundle
the wheel actually shipped, mounted into the shell the server actually
rendered.
"""

from __future__ import annotations

import os

import httpx
from playwright.sync_api import sync_playwright

DEFAULT_URL = "http://localhost:8080"


def before_all(context) -> None:
    context.base_url = os.environ.get("SHOMER_SSR_URL", DEFAULT_URL)
    context.client = httpx.Client(base_url=context.base_url, timeout=10.0)
    context.playwright = sync_playwright().start()
    context.browser = context.playwright.chromium.launch()


def before_scenario(context, scenario) -> None:
    context.page = context.browser.new_page()


def after_scenario(context, scenario) -> None:
    page = getattr(context, "page", None)
    if page is not None:
        page.close()


def after_all(context) -> None:
    for name, close in (
        ("client", "close"),
        ("browser", "close"),
        ("playwright", "stop"),
    ):
        target = getattr(context, name, None)
        if target is not None:
            getattr(target, close)()

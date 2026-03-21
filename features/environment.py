# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

import os
import subprocess
import time
import urllib.error
import urllib.request

from playwright.sync_api import sync_playwright

DEFAULT_BASE_URL = "http://localhost:8000"
MAILCATCHER_URL = os.getenv("MAILCATCHER_URL", "http://localhost:1080")


def before_scenario(context, scenario):
    """Clear state before each scenario."""
    # Clear MailCatcher inbox
    try:
        req = urllib.request.Request(MAILCATCHER_URL + "/messages", method="DELETE")
        urllib.request.urlopen(req, timeout=2)
    except Exception:
        pass
    # Clear auth state from previous scenarios
    context.bearer_token = None
    context.session_cookie = None
    context.par_request_uri = None


def before_all(context):
    context.base_url = os.getenv("BASE_URL", DEFAULT_BASE_URL)
    context.manage_compose = "BASE_URL" not in os.environ

    if context.manage_compose:
        subprocess.run(
            ["docker", "compose", "up", "-d", "--build", "--wait"],
            check=True,
        )

    for _ in range(60):
        try:
            resp = urllib.request.urlopen(context.base_url + "/readiness", timeout=5)
            if resp.status == 200:
                break
        except Exception:
            pass
        time.sleep(1)

    context.playwright = sync_playwright().start()
    context.browser = context.playwright.chromium.launch(headless=True)


def after_all(context):
    context.browser.close()
    context.playwright.stop()
    if context.manage_compose:
        subprocess.run(["docker", "compose", "down", "--volumes"], check=True)

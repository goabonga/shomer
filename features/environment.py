# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

import os
import subprocess
import time
import urllib.request

from playwright.sync_api import sync_playwright

DEFAULT_BASE_URL = "http://localhost:8000"


def before_all(context):
    context.base_url = os.getenv("BASE_URL", DEFAULT_BASE_URL)
    context.manage_compose = "BASE_URL" not in os.environ

    if context.manage_compose:
        subprocess.run(
            ["docker", "compose", "up", "-d", "--build", "--wait"],
            check=True,
        )

    for _ in range(50):
        try:
            urllib.request.urlopen(context.base_url + "/readiness")
            break
        except Exception:
            time.sleep(0.2)

    context.playwright = sync_playwright().start()
    context.browser = context.playwright.chromium.launch(headless=True)


def after_all(context):
    context.browser.close()
    context.playwright.stop()
    if context.manage_compose:
        subprocess.run(["docker", "compose", "down"], check=True)

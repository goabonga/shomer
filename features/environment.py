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

    # Warm up the Celery worker by sending a dummy registration
    # and waiting for the email to arrive in MailCatcher.
    _warmup_celery_worker(context.base_url)

    context.playwright = sync_playwright().start()
    context.browser = context.playwright.chromium.launch(headless=True)


def _warmup_celery_worker(base_url):
    """Send dummy registrations to ensure Celery worker is processing tasks.

    Performs two rounds of warmup to ensure the worker connection pool
    is fully initialized and responsive. Waits for email delivery in
    each round before proceeding.
    """
    import json
    import sys

    for probe_num in range(1, 3):
        email = f"warmup-probe-{probe_num}@example.com"
        data = json.dumps(
            {
                "email": email,
                "password": "warmup12345678",
            }
        ).encode()
        req = urllib.request.Request(
            base_url + "/auth/register",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urllib.request.urlopen(req, timeout=10)
        except Exception:
            pass

        # Wait for the email to arrive (proves the worker is warm)
        arrived = False
        for attempt in range(45):
            try:
                resp = urllib.request.urlopen(MAILCATCHER_URL + "/messages", timeout=5)
                messages = json.loads(resp.read().decode())
                if any(
                    email in r for msg in messages for r in msg.get("recipients", [])
                ):
                    arrived = True
                    break
            except Exception:
                pass
            time.sleep(1)

        if arrived:
            print(
                f"  [warmup] probe {probe_num} email arrived",
                file=sys.stderr,
            )
        else:
            print(
                f"  [warmup] WARNING: probe {probe_num} email not arrived after 45s",
                file=sys.stderr,
            )

    # Clear all warmup emails
    try:
        req = urllib.request.Request(MAILCATCHER_URL + "/messages", method="DELETE")
        urllib.request.urlopen(req, timeout=2)
    except Exception:
        pass

    # Small settling delay after warmup
    time.sleep(1)


def after_all(context):
    context.browser.close()
    context.playwright.stop()
    if context.manage_compose:
        subprocess.run(["docker", "compose", "down", "--volumes"], check=True)

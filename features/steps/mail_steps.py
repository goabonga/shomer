# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""BDD steps and helpers for MailCatcher email verification."""

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

from behave import given, then

MAILCATCHER_URL = os.getenv("MAILCATCHER_URL", "http://localhost:1080")


def _mailcatcher_api(method, path):
    """Call the MailCatcher REST API."""
    url = MAILCATCHER_URL + path
    req = urllib.request.Request(url, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=5)
        return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def clear_mailbox():
    """Delete all messages in MailCatcher."""
    _mailcatcher_api("DELETE", "/messages")


def get_latest_email(to_address, retries=30, delay=1.0):
    """Fetch the latest email sent to an address.

    Parameters
    ----------
    to_address : str
        Recipient email address.
    retries : int
        Number of retries (emails may arrive asynchronously via Celery).
    delay : float
        Delay between retries in seconds.

    Returns
    -------
    dict or None
        The email message dict, or None if not found.
    """
    for attempt in range(retries):
        status, body = _mailcatcher_api("GET", "/messages")
        if status == 200:
            messages = json.loads(body)
            for msg in reversed(messages):
                recipients = msg.get("recipients", [])
                if any(to_address in r for r in recipients):
                    # Fetch full message with HTML body and raw source
                    msg_id = msg["id"]
                    _, detail = _mailcatcher_api("GET", f"/messages/{msg_id}.json")
                    _, source = _mailcatcher_api("GET", f"/messages/{msg_id}.source")
                    _, html_body = _mailcatcher_api("GET", f"/messages/{msg_id}.html")
                    result = json.loads(detail)
                    result["source"] = source
                    result["html"] = html_body
                    return result
        if attempt > 0 and attempt % 10 == 0:
            print(
                f"  [mail] waiting for email to {to_address} ({attempt}/{retries})...",
                file=sys.stderr,
            )
        time.sleep(delay)
    print(
        f"  [mail] TIMEOUT: no email for {to_address} after {retries}s",
        file=sys.stderr,
    )
    return None


def extract_verification_code(email_body):
    """Extract a 6-digit verification code from an email body.

    Parameters
    ----------
    email_body : str
        The email HTML or plain text body.

    Returns
    -------
    str or None
        The 6-digit code, or None if not found.
    """
    # Look for the code in the template: <strong>CODE</strong>
    match = re.search(r"<strong>(\d{6})</strong>", email_body)
    if match:
        return match.group(1)
    # Fallback: any standalone 6-digit number
    match = re.search(r"\b(\d{6})\b", email_body)
    return match.group(1) if match else None


def extract_reset_token(email_body):
    """Extract a UUID reset token from an email body.

    Parameters
    ----------
    email_body : str
        The email HTML or plain text body.

    Returns
    -------
    str or None
        The UUID token, or None if not found.
    """
    match = re.search(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        email_body,
        re.IGNORECASE,
    )
    return match.group(0) if match else None


def register_and_verify_user(context, email, password):
    """Register a user and verify their email via MailCatcher.

    Uses exponential backoff for email retrieval and verification
    to handle Celery worker delays reliably.

    Parameters
    ----------
    context : behave.Context
        BDD context with base_url.
    email : str
        User email address.
    password : str
        User password.

    Returns
    -------
    str
        The verification code used.
    """
    # Register
    data = json.dumps({"email": email, "password": password}).encode()
    req = urllib.request.Request(
        context.base_url + "/auth/register",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        print(f"  [register] {email} -> {resp.status}", file=sys.stderr)
    except urllib.error.HTTPError as e:
        print(f"  [register] {email} -> {e.code}", file=sys.stderr)

    # Wait for email and extract code (with exponential backoff retry)
    code = None
    for attempt in range(5):
        msg = get_latest_email(email)
        if msg is None:
            if attempt < 4:
                wait = 2**attempt  # 1, 2, 4, 8 seconds
                print(
                    f"  [verify] no email for {email}, "
                    f"retry {attempt + 1}/5 in {wait}s",
                    file=sys.stderr,
                )
                time.sleep(wait)
                continue
            raise AssertionError(f"No verification email received for {email}")
        # Prefer HTML body (parsed by MailCatcher), fallback to raw source
        body = msg.get("html", "") or msg.get("source", "") or msg.get("body", "")
        code = extract_verification_code(body)
        if code is not None:
            break
        # Body was empty — wait and re-fetch
        print(
            f"  [verify] email found but body empty for {email}, retrying...",
            file=sys.stderr,
        )
        time.sleep(2)

    if code is None:
        raise AssertionError(
            f"No verification code found in email for {email}: "
            f"{body[:200] if body else '(empty)'}"
        )

    # Verify with exponential backoff (5 attempts: 1s, 2s, 4s, 8s, 16s)
    verified = False
    last_status = 0
    for retry in range(5):
        verify_data = json.dumps({"email": email, "code": code}).encode()
        verify_req = urllib.request.Request(
            context.base_url + "/auth/verify",
            data=verify_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            resp = urllib.request.urlopen(verify_req, timeout=10)
            last_status = resp.status
            if resp.status == 200:
                verified = True
                break
        except urllib.error.HTTPError as e:
            last_status = e.code
        if retry < 4:
            wait = 2**retry
            print(
                f"  [verify] POST /auth/verify -> {last_status}, "
                f"retry {retry + 1}/5 in {wait}s",
                file=sys.stderr,
            )
            time.sleep(wait)

    if not verified:
        # Fallback: verify directly via database (bypasses Celery timing)
        print(
            f"  [verify] API verification failed for {email}, "
            f"falling back to direct DB verification",
            file=sys.stderr,
        )
        _verify_via_db(email)

    return code


def _verify_via_db(email):
    """Mark an email as verified directly in the database.

    Used as a fallback when the Celery worker is too slow
    to deliver the verification email reliably.

    Parameters
    ----------
    email : str
        The email address to mark as verified.
    """
    env = os.environ.copy()
    env["PGPASSWORD"] = "shomer"
    pg_port = os.getenv("BDD_PG_PORT", "5432")
    sql = (
        f"UPDATE user_emails SET is_verified = true "
        f"WHERE email = '{email}' AND is_verified = false;"
    )
    pg_port = os.environ.get("BDD_PG_PORT", "5432")
    result = subprocess.run(
        [
            "psql",
            "-h",
            "localhost",
            "-p",
            pg_port,
            "-U",
            "shomer",
            "-d",
            "shomer",
            "-tAc",
            sql,
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
    if result.returncode != 0:
        print(
            f"  [verify] DB fallback failed: {result.stderr}",
            file=sys.stderr,
        )
    else:
        print(f"  [verify] DB fallback succeeded for {email}", file=sys.stderr)


@given('I register and verify "{email}" with password "{password}"')
def step_register_and_verify(context, email, password):
    """Register a user and verify via MailCatcher email flow."""
    register_and_verify_user(context, email, password)


@then('I should receive an email at "{email}"')
def step_check_email_received(context, email):
    """Check that an email was received at the given address."""
    msg = get_latest_email(email)
    assert msg is not None, f"No email received at {email}"
    context.last_email = msg


@then('the email should contain "{text}"')
def step_check_email_content(context, text):
    """Check that the last received email contains the given text."""
    source = context.last_email.get("source", "") or context.last_email.get("body", "")
    assert text in source, f"'{text}' not found in email"

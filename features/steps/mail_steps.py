# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""BDD steps and helpers for MailCatcher email verification."""

import json
import os
import re
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


def get_latest_email(to_address, retries=20, delay=1.0):
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
    for _ in range(retries):
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
        time.sleep(delay)
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
        urllib.request.urlopen(req)
    except urllib.error.HTTPError:
        pass  # 201 or duplicate — both ok

    # Wait for email and extract code (with retry for empty body)
    code = None
    for attempt in range(3):
        msg = get_latest_email(email)
        assert msg is not None, f"No verification email received for {email}"
        # Prefer HTML body (parsed by MailCatcher), fallback to raw source
        body = msg.get("html", "") or msg.get("source", "") or msg.get("body", "")
        code = extract_verification_code(body)
        if code is not None:
            break
        # Body was empty — wait and re-fetch
        time.sleep(2)
    assert code is not None, f"No verification code found in email: {body[:200]}"

    # Verify
    verify_data = json.dumps({"email": email, "code": code}).encode()
    verify_req = urllib.request.Request(
        context.base_url + "/auth/verify",
        data=verify_data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(verify_req)
    except urllib.error.HTTPError:
        pass

    return code


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

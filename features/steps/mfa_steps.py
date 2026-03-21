# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""BDD steps for MFA setup and verification flows."""

import json
import secrets
import urllib.error
import urllib.parse
import urllib.request

from behave import given


def _mfa_api(context, method, path, data=None):
    """Send an authenticated request to an MFA endpoint."""
    url = context.base_url + path
    headers = {}
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    cookie = getattr(context, "session_cookie", None)
    if cookie:
        headers["Cookie"] = f"session_id={cookie}"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


@given("a user with MFA enabled")
def step_setup_user_with_mfa(context):
    """Register a user, log in, setup MFA, and enable it.

    Stores the TOTP secret on context for generating valid codes.
    """
    from features.steps.mail_steps import register_and_verify_user

    suffix = secrets.token_hex(4)
    email = f"mfa-happy-{suffix}@example.com"
    password = "securepassword123"

    register_and_verify_user(context, email, password)

    # Log in to get session cookie
    login_data = json.dumps({"email": email, "password": password}).encode()
    login_req = urllib.request.Request(
        context.base_url + "/auth/login",
        data=login_data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        login_resp = urllib.request.urlopen(login_req, timeout=10)
        cookies = login_resp.headers.get_all("Set-Cookie") or []
        for cookie in cookies:
            if "session_id=" in cookie:
                value = cookie.split("session_id=")[1].split(";")[0]
                if value and value != '""':
                    context.session_cookie = value
    except urllib.error.HTTPError:
        pass

    # Call POST /mfa/setup
    status_code, setup_body = _mfa_api(context, "POST", "/mfa/setup")
    assert status_code == 200, f"MFA setup failed: {status_code} {setup_body}"
    context.mfa_totp_secret = setup_body["secret"]

    # Generate a valid TOTP code
    from shomer.services.mfa_service import MFAService

    totp_code = MFAService.generate_totp_code(context.mfa_totp_secret)

    # Call POST /mfa/enable with the TOTP code
    status_code, enable_body = _mfa_api(
        context, "POST", "/mfa/enable", {"code": totp_code}
    )
    assert status_code == 200, f"MFA enable failed: {status_code} {enable_body}"
    assert enable_body["mfa_enabled"] is True
    context.mfa_backup_codes = enable_body.get("backup_codes", [])

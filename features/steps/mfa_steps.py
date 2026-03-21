# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""BDD steps for MFA setup and verification flows."""

import base64
import hashlib
import hmac
import json
import secrets
import struct
import time
import urllib.error
import urllib.parse
import urllib.request

from behave import given


def _generate_totp_code(secret, time_offset=0):
    """Generate a TOTP code (RFC 6238) without importing server code."""
    key = base64.b32decode(secret, casefold=True)
    counter = int(time.time()) // 30 + time_offset
    counter_bytes = struct.pack(">Q", counter)
    mac = hmac.new(key, counter_bytes, hashlib.sha1).digest()
    offset = mac[-1] & 0x0F
    truncated = struct.unpack(">I", mac[offset : offset + 4])[0] & 0x7FFFFFFF
    code = truncated % (10**6)
    return str(code).zfill(6)


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

    # Generate a valid TOTP code (stdlib only, no server imports)
    totp_code = _generate_totp_code(context.mfa_totp_secret)

    # Call POST /mfa/enable with the TOTP code
    status_code, enable_body = _mfa_api(
        context, "POST", "/mfa/enable", {"code": totp_code}
    )
    assert status_code == 200, f"MFA enable failed: {status_code} {enable_body}"
    assert enable_body["mfa_enabled"] is True
    context.mfa_backup_codes = enable_body.get("backup_codes", [])

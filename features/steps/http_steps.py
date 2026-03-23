# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

import json
import urllib.error
import urllib.parse
import urllib.request

from behave import given, then, when


def _send(context, method, path, data=None):
    """Send an HTTP request and store response on context."""
    url = context.base_url + path
    headers = {}
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    # Attach Bearer token if available
    bearer = getattr(context, "bearer_token", None)
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    # Attach session cookie if available
    cookie = getattr(context, "session_cookie", None)
    if cookie:
        headers["Cookie"] = f"session_id={cookie}"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        context.response = urllib.request.urlopen(req, timeout=10)
        context.response_status = context.response.status
        context.response_body = context.response.read().decode()
        _capture_session_cookie(context, context.response)
    except urllib.error.HTTPError as e:
        context.response = e
        context.response_status = e.code
        context.response_body = e.read().decode()
        _capture_session_cookie(context, e)
    except urllib.error.URLError as e:
        context.response = None
        context.response_status = 0
        context.response_body = str(e)
    _capture_mfa_token(context)


def _capture_session_cookie(context, response):
    """Extract session_id cookie from Set-Cookie header.

    Handles edge cases: quoted values, whitespace, multiple headers.
    """
    raw_headers = response.headers.get_all("Set-Cookie") or []
    for cookie in raw_headers:
        if "session_id=" in cookie:
            value = cookie.split("session_id=")[1].split(";")[0].strip()
            # Strip surrounding quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            if value:
                context.session_cookie = value


def _capture_mfa_token(context):
    """Extract mfa_token from response body if present."""
    body = getattr(context, "response_body", "")
    if body and '"mfa_token"' in body:
        try:
            data = json.loads(body)
            if "mfa_token" in data:
                context.mfa_login_token = data["mfa_token"]
        except (json.JSONDecodeError, ValueError):
            pass


@given("I have a JSON payload")
def step_set_json_payload(context):
    context.json_payload = json.loads(context.text)


def _substitute_vars(context, text):
    """Replace ${variable} placeholders with context values."""
    auth_code = getattr(context, "oauth2_auth_code", None)
    if auth_code and "${auth_code}" in text:
        text = text.replace("${auth_code}", auth_code)
    bearer = getattr(context, "bearer_token", None)
    if bearer and "${bearer_token}" in text:
        text = text.replace("${bearer_token}", bearer)
    dc = getattr(context, "device_code", None)
    if dc and "${device_code}" in text:
        text = text.replace("${device_code}", dc)
    par_uri = getattr(context, "par_request_uri", None)
    if par_uri and "${request_uri}" in text:
        text = text.replace("${request_uri}", urllib.parse.quote(par_uri, safe=""))
    jar_jwt = getattr(context, "jar_request_jwt", None)
    if jar_jwt and "${jar_request_jwt}" in text:
        text = text.replace("${jar_request_jwt}", urllib.parse.quote(jar_jwt, safe=""))
    exc_tok = getattr(context, "exchange_subject_token", None)
    if exc_tok and "${exchange_subject_token}" in text:
        text = text.replace("${exchange_subject_token}", exc_tok)
    # MFA: generate a fresh TOTP code on demand (stdlib only)
    mfa_secret = getattr(context, "mfa_totp_secret", None)
    if mfa_secret and "${mfa_totp_code}" in text:
        from features.steps.mfa_steps import _generate_totp_code

        text = text.replace("${mfa_totp_code}", _generate_totp_code(mfa_secret))
    mfa_backup = getattr(context, "mfa_backup_codes", None)
    if mfa_backup and "${mfa_backup_code}" in text:
        text = text.replace("${mfa_backup_code}", mfa_backup[0])
    mfa_email = getattr(context, "mfa_user_email", None)
    if mfa_email and "${mfa_user_email}" in text:
        text = text.replace("${mfa_user_email}", mfa_email)
    mfa_login_tok = getattr(context, "mfa_login_token", None)
    if mfa_login_tok and "${mfa_login_token}" in text:
        text = text.replace("${mfa_login_token}", mfa_login_tok)
    fed_slug = getattr(context, "federation_tenant_slug", None)
    if fed_slug and "${federation_tenant_slug}" in text:
        text = text.replace("${federation_tenant_slug}", fed_slug)
    fed_idp = getattr(context, "federation_idp_id", None)
    if fed_idp and "${federation_idp_id}" in text:
        text = text.replace("${federation_idp_id}", fed_idp)
    return text


@when('I send a GET request to "{path}"')
def step_get_request(context, path):
    path = _substitute_vars(context, path)
    _send(context, "GET", path)


@when('I send a POST request to "{path}"')
def step_post_request(context, path):
    data = getattr(context, "json_payload", None)
    _send(context, "POST", path, data=data)
    context.json_payload = None


@when('I send a POST request to "{path}" with JSON')
def step_post_request_with_json(context, path):
    text = _substitute_vars(context, context.text)
    data = json.loads(text)
    _send(context, "POST", path, data=data)


@when('I send a PUT request to "{path}"')
def step_put_request(context, path):
    data = getattr(context, "json_payload", None)
    _send(context, "PUT", path, data=data)
    context.json_payload = None


@when('I send a PUT request to "{path}" with JSON')
def step_put_request_with_json(context, path):
    data = json.loads(context.text)
    _send(context, "PUT", path, data=data)


def _send_form(context, path, form_data):
    """Send a form-encoded POST request."""
    url = context.base_url + path
    body = urllib.parse.urlencode(form_data).encode()
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    cookie = getattr(context, "session_cookie", None)
    if cookie:
        headers["Cookie"] = f"session_id={cookie}"
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        context.response = urllib.request.urlopen(req, timeout=10)
        context.response_status = context.response.status
        context.response_body = context.response.read().decode()
        _capture_session_cookie(context, context.response)
    except urllib.error.HTTPError as e:
        context.response = e
        context.response_status = e.code
        context.response_body = e.read().decode()
        _capture_session_cookie(context, e)
    except urllib.error.URLError as e:
        context.response = None
        context.response_status = 0
        context.response_body = str(e)
    _capture_mfa_token(context)


@when('I send a form POST to "{path}" with')
def step_post_form(context, path):
    text = _substitute_vars(context, context.text)
    form_data = json.loads(text)
    _send_form(context, path, form_data)


@given('a registered and verified user "{email}" with password "{password}"')
def step_registered_verified_user(context, email, password):
    """Register and verify a user via the API + MailCatcher."""
    import time as _time

    from features.steps.mail_steps import register_and_verify_user

    register_and_verify_user(context, email, password)
    # Allow DB commit to complete before dependent steps
    _time.sleep(0.3)


@given('I am logged in as "{email}" with password "{password}"')
def step_logged_in_as(context, email, password):
    """Log in via POST /auth/login and capture the session cookie.

    Retries up to 5 times with exponential backoff on 401/403
    (email not verified yet) to handle Celery timing.
    """
    import sys as _sys
    import time as _time

    for attempt in range(5):
        _send(context, "POST", "/auth/login", {"email": email, "password": password})
        if context.response_status == 200:
            if not getattr(context, "session_cookie", None):
                _sys.stderr.write(
                    f"  [login] WARNING: 200 but no session cookie for {email}\n"
                )
            # Allow DB commit to complete (yield-dependency race condition)
            _time.sleep(0.3)
            return
        if context.response_status in (401, 403):
            wait = 2**attempt
            _sys.stderr.write(
                f"  [login] {email} -> {context.response_status}, "
                f"retry {attempt + 1}/5 in {wait}s\n"
            )
            _time.sleep(wait)
            continue
        break
    assert context.response_status == 200, (
        f"Login failed with status {context.response_status}: {context.response_body}"
    )


@given("I have a Bearer token for the OAuth2 client")
def step_obtain_bearer_token(context):
    """Obtain a Bearer token via password grant for the BDD test user/client.

    Retries up to 3 times with backoff to handle timing issues when
    the user's email verification hasn't fully propagated yet.
    """
    import time as _time

    form_data = {
        "grant_type": "password",
        "username": context.oauth2_user_email,
        "password": context.oauth2_user_password,
        "client_id": context.oauth2_client_id,
        "client_secret": context.oauth2_client_secret,
        "scope": "openid profile email",
    }
    for attempt in range(3):
        _send_form(context, "/oauth2/token", form_data)
        if context.response_status == 200:
            break
        if context.response_status in (400, 401, 403) and attempt < 2:
            _time.sleep(2**attempt)
            continue
        break
    assert context.response_status == 200, (
        f"Token request failed: {context.response_body}"
    )
    token_data = json.loads(context.response_body)
    context.bearer_token = token_data["access_token"]
    # Allow DB commit to complete (yield-dependency race condition)
    _time.sleep(0.3)


@when('I send a DELETE request to "{path}"')
def step_delete_request(context, path):
    _send(context, "DELETE", path)


@then("I wait {seconds:d} seconds")
@given("I wait {seconds:d} seconds")  # type: ignore[no-redef]
def step_wait_seconds(context, seconds):
    """Pause execution for a fixed number of seconds."""
    import time as _time

    _time.sleep(seconds)


@then("the response status code should be {status_code:d}")
def step_check_status_code(context, status_code):
    body_preview = getattr(context, "response_body", "")[:300]
    assert context.response_status == status_code, (
        f"Expected {status_code}, got {context.response_status}. Body: {body_preview}"
    )


@then('the response body should contain "{text}"')
def step_check_response_body(context, text):
    assert text in context.response_body


@then('the response should have JSON key "{key}"')
def step_check_json_key(context, key):
    data = json.loads(context.response_body)
    assert key in data, f"Key '{key}' not found in {data}"


@then("the response content type should be html")
def step_check_html_content_type(context):
    content_type = context.response.headers.get("Content-Type", "")
    assert "text/html" in content_type


@then("the response content type should be json")
def step_check_json_content_type(context):
    content_type = context.response.headers.get("Content-Type", "")
    assert "application/json" in content_type


@then('the response should have header "{name}" containing "{value}"')
def step_check_response_header(context, name, value):
    header = context.response.headers.get(name, "")
    assert value in header, f"Header '{name}' = '{header}' does not contain '{value}'"

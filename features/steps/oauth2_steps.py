# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""BDD steps for OAuth2 consent flow setup."""

import json
import os
import subprocess
import urllib.error
import urllib.request

from behave import given


def _api(context, method, path, data=None):
    """Send an API request and return (status, body_text)."""
    url = context.base_url + path
    headers = {}
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req)
        return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def _psql(sql):
    """Run SQL against PostgreSQL on localhost:5432."""
    env = os.environ.copy()
    env["PGPASSWORD"] = "shomer"
    result = subprocess.run(
        ["psql", "-h", "localhost", "-U", "shomer", "-d", "shomer", "-tAc", sql],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
    assert result.returncode == 0, f"psql failed: {result.stderr}"
    return result.stdout.strip()


@given("an authenticated user with an OAuth2 client")
def step_setup_oauth2_flow(context):
    """Register a verified user and create an OAuth2 client in the DB.

    The user will authenticate via Playwright during the consent flow
    (redirect to login → fill credentials → submit).
    """
    email = "oauth2-bdd@example.com"
    password = "securepassword123"

    # 1. Register user via API (idempotent — returns 201 even if exists)
    _api(
        context,
        "POST",
        "/auth/register",
        {
            "email": email,
            "password": password,
        },
    )

    # 2. Verify email directly in PostgreSQL
    _psql(
        "UPDATE user_emails SET is_verified = true, "
        "verified_at = NOW() WHERE email = 'oauth2-bdd@example.com';"
    )

    # 3. Create OAuth2 client directly in PostgreSQL
    _psql(
        "INSERT INTO oauth2_clients "
        "(id, client_id, client_name, client_type, "
        "redirect_uris, grant_types, response_types, scopes, contacts, "
        "token_endpoint_auth_method, is_active, created_at, updated_at) "
        "VALUES ("
        "gen_random_uuid(), 'bdd-test-client', 'BDD Test App', 'CONFIDENTIAL', "
        "'[\"https://app.example.com/callback\"]'::jsonb, "
        "'[\"authorization_code\"]'::jsonb, "
        "'[\"code\"]'::jsonb, "
        '\'["openid", "profile"]\'::jsonb, '
        "'[]'::jsonb, "
        "'CLIENT_SECRET_BASIC', true, NOW(), NOW()"
        ") ON CONFLICT (client_id) DO NOTHING;"
    )

    context.oauth2_client_id = "bdd-test-client"

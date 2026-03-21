# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""BDD steps for OAuth2 consent flow setup."""

import os
import subprocess

from behave import given
from features.steps.mail_steps import register_and_verify_user


def _psql(sql):
    """Run SQL against PostgreSQL on localhost:5432 (for OAuth2 client seeding only)."""
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


def _hash_secret(secret):
    """Hash a client secret with argon2id via Python (for psql seeding)."""
    from shomer.core.security import hash_password

    return hash_password(secret)


@given("an authenticated user with an OAuth2 client")
def step_setup_oauth2_flow(context):
    """Register a verified user (via MailCatcher) and create an OAuth2 client.

    The user will authenticate via Playwright during the consent flow.
    """
    email = "oauth2-bdd@example.com"
    password = "securepassword123"

    # 0. Clean up any existing user (idempotent reruns)
    _psql(
        "DELETE FROM users WHERE id IN "
        "(SELECT user_id FROM user_emails WHERE email = 'oauth2-bdd@example.com');"
    )

    # 1. Register and verify user via API + MailCatcher email flow
    register_and_verify_user(context, email, password)

    # 2. Create OAuth2 client via psql (no admin API yet)
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


@given("a public OAuth2 client")
def step_setup_public_client(context):
    """Create a public OAuth2 client (no secret, auth_method=NONE)."""
    _psql(
        "INSERT INTO oauth2_clients "
        "(id, client_id, client_name, client_type, "
        "redirect_uris, grant_types, response_types, scopes, contacts, "
        "token_endpoint_auth_method, is_active, created_at, updated_at) "
        "VALUES ("
        "gen_random_uuid(), 'bdd-public-client', 'BDD Public App', 'PUBLIC', "
        "'[\"https://app.example.com/callback\"]'::jsonb, "
        "'[\"authorization_code\"]'::jsonb, "
        "'[\"code\"]'::jsonb, "
        '\'["openid", "profile"]\'::jsonb, '
        "'[]'::jsonb, "
        "'NONE', true, NOW(), NOW()"
        ") ON CONFLICT (client_id) DO NOTHING;"
    )
    context.oauth2_client_id = "bdd-public-client"


@given("a verified user and an OAuth2 client with all grants")
def step_setup_oauth2_full(context):
    """Create a verified user and a confidential OAuth2 client with all grant types.

    Stores client_id and client_secret on context for token requests.
    """
    email = "token-bdd@example.com"
    password = "securepassword123"

    _psql(
        "DELETE FROM users WHERE id IN "
        "(SELECT user_id FROM user_emails WHERE email = 'token-bdd@example.com');"
    )

    register_and_verify_user(context, email, password)

    secret = "bdd-test-secret-value"
    secret_hash = _hash_secret(secret)

    # Escape single quotes in the hash for SQL
    escaped_hash = secret_hash.replace("'", "''")

    _psql(
        "INSERT INTO oauth2_clients "
        "(id, client_id, client_secret_hash, client_name, client_type, "
        "redirect_uris, grant_types, response_types, scopes, contacts, "
        "token_endpoint_auth_method, is_active, created_at, updated_at) "
        "VALUES ("
        "gen_random_uuid(), 'bdd-full-client', "
        f"'{escaped_hash}', "
        "'BDD Full App', 'CONFIDENTIAL', "
        "'[\"https://app.example.com/callback\"]'::jsonb, "
        '\'["authorization_code", "client_credentials", "password", "refresh_token"]\'::jsonb, '
        "'[\"code\"]'::jsonb, "
        '\'["openid", "profile", "email"]\'::jsonb, '
        "'[]'::jsonb, "
        "'CLIENT_SECRET_POST', true, NOW(), NOW()"
        ") ON CONFLICT (client_id) DO UPDATE SET "
        f"client_secret_hash = '{escaped_hash}', "
        "grant_types = "
        '\'["authorization_code", "client_credentials", "password", "refresh_token"]\'::jsonb;'
    )

    context.oauth2_client_id = "bdd-full-client"
    context.oauth2_client_secret = secret
    context.oauth2_user_email = email
    context.oauth2_user_password = password


@given("an authorization code for the OAuth2 client")
def step_create_auth_code(context):
    """Insert an authorization code in the DB for the test client/user.

    Requires ``a verified user and an OAuth2 client with all grants``
    to have run first. Stores the code on ``context.oauth2_auth_code``.
    """
    import secrets

    code = secrets.token_urlsafe(32)

    # Get user_id from the DB
    user_id = _psql(
        "SELECT u.id FROM users u "
        "JOIN user_emails ue ON ue.user_id = u.id "
        f"WHERE ue.email = '{context.oauth2_user_email}';"
    )
    assert user_id, "User not found in DB"

    _psql(
        "INSERT INTO authorization_codes "
        "(id, code, user_id, client_id, redirect_uri, scopes, "
        "expires_at, is_used, created_at, updated_at) "
        "VALUES ("
        f"gen_random_uuid(), '{code}', '{user_id}', "
        f"'{context.oauth2_client_id}', "
        "'https://app.example.com/callback', 'openid profile', "
        "NOW() + INTERVAL '10 minutes', false, NOW(), NOW()"
        ");"
    )

    context.oauth2_auth_code = code


@given("an approved device code for the OAuth2 client")
def step_create_approved_device_code(context):
    """Create a device code via API, then approve it in the DB.

    Requires ``a verified user and an OAuth2 client with all grants``
    to have run first. Stores the device_code on ``context.device_code``.
    """
    import json
    import urllib.error
    import urllib.parse
    import urllib.request

    # 1. Create device code via POST /oauth2/device
    form_data = urllib.parse.urlencode(
        {
            "scope": "openid profile",
            "client_id": context.oauth2_client_id,
            "client_secret": context.oauth2_client_secret,
        }
    ).encode()
    req = urllib.request.Request(
        context.base_url + "/oauth2/device",
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    resp = urllib.request.urlopen(req, timeout=10)
    body = json.loads(resp.read().decode())
    device_code = body["device_code"]
    context.device_code = device_code

    # 2. Get user_id
    user_id = _psql(
        "SELECT u.id FROM users u "
        "JOIN user_emails ue ON ue.user_id = u.id "
        f"WHERE ue.email = '{context.oauth2_user_email}';"
    )
    assert user_id, "User not found in DB"

    # 3. Approve the device code in the DB
    _psql(
        f"UPDATE device_codes SET status = 'APPROVED', user_id = '{user_id}' "
        f"WHERE device_code = '{device_code}';"
    )

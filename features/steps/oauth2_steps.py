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

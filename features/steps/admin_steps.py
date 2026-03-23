# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""BDD steps for admin user setup with RBAC scopes."""

import os
import subprocess
import time

from behave import given
from features.steps.mail_steps import register_and_verify_user


def _psql(sql):
    """Run SQL against the BDD PostgreSQL instance."""
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


@given('an admin user "{email}" with password "{password}"')
def step_setup_admin_user(context, email, password):
    """Register, verify, and grant admin:users:read scope to a user.

    Seeds the role, scope, role_scope, and user_role tables via psql.
    """
    register_and_verify_user(context, email, password)
    time.sleep(0.3)

    # Get the user ID
    user_id = _psql(
        f"SELECT u.id FROM users u "
        f"JOIN user_emails ue ON ue.user_id = u.id "
        f"WHERE ue.email = '{email}';"
    )
    assert user_id, f"User {email} not found in DB"

    # Seed role
    _psql(
        "INSERT INTO roles (id, name, description, is_system, created_at, updated_at) "
        "VALUES (gen_random_uuid(), 'admin', 'Administrator', true, NOW(), NOW()) "
        "ON CONFLICT (name) DO NOTHING;"
    )

    # Link role to all admin scopes
    admin_scopes = (
        "admin:users:read",
        "admin:users:write",
        "admin:clients:read",
        "admin:clients:write",
        "admin:sessions:read",
        "admin:sessions:write",
    )
    for scope_name in admin_scopes:
        _psql(
            "INSERT INTO scopes (id, name, description, created_at, updated_at) "
            f"VALUES (gen_random_uuid(), '{scope_name}', '{scope_name}', NOW(), NOW()) "
            "ON CONFLICT (name) DO NOTHING;"
        )
        _psql(
            f"INSERT INTO role_scopes (id, role_id, scope_id, created_at, updated_at) "
            f"SELECT gen_random_uuid(), r.id, s.id, NOW(), NOW() "
            f"FROM roles r, scopes s "
            f"WHERE r.name = 'admin' AND s.name = '{scope_name}' "
            f"ON CONFLICT ON CONSTRAINT uq_role_scope DO NOTHING;"
        )

    # Assign role to user
    _psql(
        f"INSERT INTO user_roles (id, user_id, role_id, tenant_id, created_at, updated_at) "
        f"SELECT gen_random_uuid(), '{user_id}', r.id, NULL, NOW(), NOW() "
        f"FROM roles r WHERE r.name = 'admin' "
        f"ON CONFLICT ON CONSTRAINT uq_user_role_tenant DO NOTHING;"
    )

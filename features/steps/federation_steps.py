# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""BDD steps for federation provider setup."""

import os
import subprocess

from behave import given


def _psql(sql):
    """Run SQL against the BDD PostgreSQL instance."""
    env = os.environ.copy()
    env["PGPASSWORD"] = "shomer"
    pg_port = os.getenv("BDD_PG_PORT", "5432")
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
    assert result.returncode == 0, f"psql failed: {result.stderr}"
    return result.stdout.strip()


@given("a tenant with an identity provider")
def step_setup_tenant_with_idp(context):
    """Create a tenant and an active IdP for BDD testing.

    Seeds the DB directly via psql. Stores tenant_slug and idp_id
    on context for subsequent steps.
    """
    # Upsert tenant
    _psql(
        "INSERT INTO tenants "
        "(id, slug, name, display_name, is_active, is_platform, trust_mode, settings, "
        "created_at, updated_at) "
        "VALUES ("
        "gen_random_uuid(), 'bdd-federation', 'BDD Federation Tenant', "
        "'BDD Federation', true, false, 'none', '{}', NOW(), NOW()"
        ") ON CONFLICT (slug) DO UPDATE SET is_active = true;"
    )

    tenant_id = _psql("SELECT id FROM tenants WHERE slug = 'bdd-federation';")
    assert tenant_id, "Tenant not found"

    # Delete existing IdP to avoid conflicts, then insert fresh
    _psql(
        f"DELETE FROM identity_providers "
        f"WHERE tenant_id = '{tenant_id}' AND name = 'BDD Google';"
    )
    _psql(
        f"INSERT INTO identity_providers "
        f"(id, tenant_id, name, provider_type, client_id, "
        f"discovery_url, scopes, is_active, is_default, auto_provision, allow_linking, "
        f"display_order, created_at, updated_at) "
        f"VALUES ("
        f"gen_random_uuid(), '{tenant_id}', 'BDD Google', 'GOOGLE', "
        f"'bdd-google-client-id', "
        f"'https://accounts.google.com/.well-known/openid-configuration', "
        f'\'["openid", "profile", "email"]\'::jsonb, '
        f"true, false, true, true, "
        f"0, NOW(), NOW()"
        f");"
    )

    idp_id = _psql(
        f"SELECT id FROM identity_providers "
        f"WHERE tenant_id = '{tenant_id}' AND name = 'BDD Google';"
    )
    assert idp_id, "IdP not found after insert"

    context.federation_tenant_slug = "bdd-federation"
    context.federation_idp_id = idp_id

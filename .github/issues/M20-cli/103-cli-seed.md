# feat(cli): shomer seed — initial data seeding (superadmin, roles, scopes, client)

## Description

CLI command to seed the database with initial data required for a fresh deployment: superadmin user, system roles and scopes, default OAuth2 client, and initial JWK.

## Objective

Enable one-command bootstrap of a new Shomer deployment.

## Tasks

- [ ] `shomer seed` — run all seeders
- [ ] `shomer seed superadmin` — create superadmin user (interactive email/password prompt)
- [ ] `shomer seed roles` — create system roles (super_admin, admin, user_manager, etc.)
- [ ] `shomer seed scopes` — create system scopes
- [ ] `shomer seed client` — create default first-party OAuth2 client
- [ ] `shomer seed jwks` — generate initial RSA signing key
- [ ] Idempotent: skip existing records
- [ ] `--force` flag to reset and recreate
- [ ] Unit tests

## Dependencies

- #4 — User model
- #71 — RBAC models
- #27 — OAuth2Client model
- #11 — JWK model

## Labels

`type:infra`, `feature:rbac`, `size:M`

## feat(cli): shomer seed - initial data seeding (superadmin, roles, scopes, client)

## Summary

CLI command to seed the database with initial data required for a fresh deployment: superadmin user, system roles and scopes, default OAuth2 client, and initial JWK.

## Changes

- [ ] `shomer seed` - run all seeders
- [ ] `shomer seed superadmin` - create superadmin user (interactive email/password prompt)
- [ ] `shomer seed roles` - create system roles (super_admin, admin, user_manager, etc.)
- [ ] `shomer seed scopes` - create system scopes
- [ ] `shomer seed client` - create default first-party OAuth2 client
- [ ] `shomer seed jwks` - generate initial RSA signing key
- [ ] Idempotent: skip existing records
- [ ] `--force` flag to reset and recreate
- [ ] Unit tests

## Dependencies

- #4 - User model
- #71 - RBAC models
- #27 - OAuth2Client model
- #11 - JWK model

## Related Issue

Closes #103

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



## feat(cli): shomer user - user management commands

## Summary

CLI commands for user administration: list users, view details, create, activate/deactivate, delete, reset password, and manage roles.

## Changes

- [ ] `shomer user list` - list users (with filters: --active, --email, --tenant, pagination)
- [ ] `shomer user get <id|email>` - show user details (profile, emails, roles, MFA status)
- [ ] `shomer user create` - create user (--email, --password, --username, --verified)
- [ ] `shomer user activate <id|email>` - activate user
- [ ] `shomer user deactivate <id|email>` - deactivate user
- [ ] `shomer user delete <id|email>` - delete user (with --confirm)
- [ ] `shomer user reset-password <id|email>` - set new password
- [ ] `shomer user add-role <id|email> <role>` - assign role
- [ ] `shomer user remove-role <id|email> <role>` - remove role
- [ ] Rich table output
- [ ] Unit tests

## Dependencies

- #4 - User model
- #88 - admin user logic (shared service layer)

## Related Issue

Closes #104

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



## feat(cli): shomer role/scope - RBAC management commands

## Summary

CLI commands for role and scope management: CRUD for roles and scopes, assign/remove scopes to roles, view role details with assigned scopes.

## Changes

- [ ] `shomer scope list` - list all scopes
- [ ] `shomer scope create <name>` - create scope (--description)
- [ ] `shomer scope delete <name>` - delete scope (with --confirm)
- [ ] `shomer role list` - list all roles with scope count
- [ ] `shomer role get <name>` - show role details with assigned scopes
- [ ] `shomer role create <name>` - create role (--description)
- [ ] `shomer role delete <name>` - delete role (with --confirm)
- [ ] `shomer role add-scope <role> <scope>` - assign scope to role
- [ ] `shomer role remove-scope <role> <scope>` - remove scope from role
- [ ] Rich table output
- [ ] Unit tests

## Dependencies

- #71 - RBAC models
- #72 - permission service

## Related Issue

Closes #108

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



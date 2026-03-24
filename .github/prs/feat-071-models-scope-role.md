## feat(models): Scope, Role, RoleScope, UserRole

## Summary

RBAC models: Scope (name, description), Role (name, description, is_system), RoleScope (many-to-many), UserRole (user_id, role_id, tenant_id, expires_at).

## Changes

- [ ] Scope model (name with dot notation e.g. "admin:users:read", description)
- [ ] Role model (name, description, is_system flag)
- [ ] RoleScope junction table
- [ ] UserRole model (user_id, role_id, tenant_id, expires_at)
- [ ] Relationships and indexes
- [ ] Alembic migration

## Dependencies

- #3 - declarative base
- #4 - User model

## Related Issue

Closes #71

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



## feat(rbac): permission evaluation service (wildcard, expiration)

## Summary

RBAC service for evaluating permissions: resolves user roles, checks scope membership with wildcard support (e.g., "admin:*" matches "admin:users:read"), respects role expiration.

## Changes

- [ ] Resolve roles for user + tenant
- [ ] Collect scopes from all active roles
- [ ] Wildcard scope matching (e.g., "admin:*")
- [ ] Role expiration check
- [ ] `has_permission(user_id, scope, tenant_id)` method
- [ ] `has_any_permission(user_id, scopes, tenant_id)` method
- [ ] Unit tests with wildcard and expiration scenarios

## Dependencies

- #71 - RBAC models

## Related Issue

Closes #72

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



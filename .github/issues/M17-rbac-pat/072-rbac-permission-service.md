# feat(rbac): permission evaluation service (wildcard, expiration)

## Description

RBAC service for evaluating permissions: resolves user roles, checks scope membership with wildcard support (e.g., "admin:*" matches "admin:users:read"), respects role expiration.

## Objective

Provide a fast, cacheable permission check used by the RBAC middleware.

## Tasks

- [ ] Resolve roles for user + tenant
- [ ] Collect scopes from all active roles
- [ ] Wildcard scope matching (e.g., "admin:*")
- [ ] Role expiration check
- [ ] `has_permission(user_id, scope, tenant_id)` method
- [ ] `has_any_permission(user_id, scopes, tenant_id)` method
- [ ] Unit tests with wildcard and expiration scenarios

## Dependencies

- #71 — RBAC models

## Labels

`feature:rbac`, `type:service`, `size:M`

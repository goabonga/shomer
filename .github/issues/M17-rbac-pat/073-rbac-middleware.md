# feat(rbac): RBAC authorization middleware

## Description

FastAPI middleware/dependency for route-level authorization. Checks that the current user has the required scope(s) for the requested route. Returns 403 on insufficient permissions.

## Objective

Enforce role-based access control on protected routes (especially admin routes).

## Tasks

- [ ] `require_scope("scope:name")` dependency
- [ ] `require_any_scope(["scope:a", "scope:b"])` dependency
- [ ] Integration with get_current_user
- [ ] 403 Forbidden response with clear error message
- [ ] Unit tests

## Dependencies

- #72 — permission evaluation service
- #20 — session service (for user context)

## Labels

`feature:rbac`, `type:infra`, `size:M`

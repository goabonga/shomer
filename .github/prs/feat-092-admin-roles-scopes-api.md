## feat(admin): roles and scopes API (/admin/roles, /admin/scopes)

## Summary

Admin API for role and scope management: CRUD for roles, CRUD for scopes, assign/remove scopes to roles, assign/remove roles to users.

## Changes

- [ ] GET/POST `/admin/scopes` - list and create scopes
- [ ] PUT/DELETE `/admin/scopes/{id}` - update and delete scopes
- [ ] GET/POST `/admin/roles` - list and create roles
- [ ] PUT/DELETE `/admin/roles/{id}` - update and delete roles
- [ ] POST/DELETE `/admin/roles/{id}/scopes/{scope_id}` - assign/remove scope
- [ ] POST/DELETE `/admin/users/{id}/roles/{role_id}` - assign/remove role
- [ ] RBAC protection
- [ ] Integration tests

## Dependencies

- #71 - RBAC models
- #73 - RBAC middleware

## Related Issue

Closes #92

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



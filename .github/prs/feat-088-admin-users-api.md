## feat(admin): CRUD users API (/admin/users)

## Summary

Admin API for user management: list (with filters, pagination), get by ID (with roles, emails, sessions, tenant memberships), create, update (activate/deactivate, set roles), delete.

## Changes

- [ ] GET `/admin/users` - list with search, filter, pagination
- [ ] GET `/admin/users/{id}` - detailed user view (roles, emails, sessions, memberships)
- [ ] POST `/admin/users` - create user (admin bypass for email verification)
- [ ] PUT `/admin/users/{id}` - update user (is_active, roles, profile)
- [ ] DELETE `/admin/users/{id}` - soft delete or deactivate
- [ ] RBAC protection (require admin scope)
- [ ] Integration tests

## Dependencies

- #4 - User model
- #71 - RBAC models
- #73 - RBAC middleware

## Related Issue

Closes #88

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



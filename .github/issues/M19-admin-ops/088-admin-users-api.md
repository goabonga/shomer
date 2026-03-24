# feat(admin): CRUD users API (/admin/users)

## Description

Admin API for user management: list (with filters, pagination), get by ID (with roles, emails, sessions, tenant memberships), create, update (activate/deactivate, set roles), delete.

## Objective

Provide full user administration for operators and tenant admins.

## Tasks

- [ ] GET `/admin/users` — list with search, filter, pagination
- [ ] GET `/admin/users/{id}` — detailed user view (roles, emails, sessions, memberships)
- [ ] POST `/admin/users` — create user (admin bypass for email verification)
- [ ] PUT `/admin/users/{id}` — update user (is_active, roles, profile)
- [ ] DELETE `/admin/users/{id}` — soft delete or deactivate
- [ ] RBAC protection (require admin scope)
- [ ] Integration tests

## Dependencies

- #4 — User model
- #71 — RBAC models
- #73 — RBAC middleware

## Labels

`feature:admin`, `type:route`, `layer:api`, `size:L`

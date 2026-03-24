# feat(admin): roles and scopes API (/admin/roles, /admin/scopes)

## Description

Admin API for role and scope management: CRUD for roles, CRUD for scopes, assign/remove scopes to roles, assign/remove roles to users.

## Objective

Allow administrators to configure the RBAC system.

## Tasks

- [ ] GET/POST `/admin/scopes` — list and create scopes
- [ ] PUT/DELETE `/admin/scopes/{id}` — update and delete scopes
- [ ] GET/POST `/admin/roles` — list and create roles
- [ ] PUT/DELETE `/admin/roles/{id}` — update and delete roles
- [ ] POST/DELETE `/admin/roles/{id}/scopes/{scope_id}` — assign/remove scope
- [ ] POST/DELETE `/admin/users/{id}/roles/{role_id}` — assign/remove role
- [ ] RBAC protection
- [ ] Integration tests

## Dependencies

- #71 — RBAC models
- #73 — RBAC middleware

## Labels

`feature:admin`, `feature:rbac`, `type:route`, `layer:api`, `size:L`

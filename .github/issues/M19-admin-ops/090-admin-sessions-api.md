# feat(admin): sessions API (/admin/sessions)

## Description

Admin API for session management: list active sessions (with filters by user, tenant), view session details, revoke sessions.

## Objective

Give administrators visibility and control over active user sessions.

## Tasks

- [ ] GET `/admin/sessions` — list with filters (user_id, tenant_id)
- [ ] GET `/admin/sessions/{id}` — session details
- [ ] DELETE `/admin/sessions/{id}` — revoke session
- [ ] DELETE `/admin/users/{id}/sessions` — revoke all sessions for a user
- [ ] RBAC protection
- [ ] Integration tests

## Dependencies

- #6 — Session model
- #73 — RBAC middleware

## Labels

`feature:admin`, `type:route`, `layer:api`, `size:M`

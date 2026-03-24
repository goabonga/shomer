# feat(admin): PATs API (/admin/pats)

## Description

Admin API for PAT oversight: list all PATs (across users), view details, revoke any PAT.

## Objective

Give administrators visibility and control over all personal access tokens.

## Tasks

- [ ] GET `/admin/pats` — list all PATs with filters (user_id, scope)
- [ ] GET `/admin/pats/{id}` — PAT details
- [ ] DELETE `/admin/pats/{id}` — revoke PAT
- [ ] RBAC protection
- [ ] Integration tests

## Dependencies

- #74 — PAT model
- #73 — RBAC middleware

## Labels

`feature:admin`, `feature:pat`, `type:route`, `layer:api`, `size:S`

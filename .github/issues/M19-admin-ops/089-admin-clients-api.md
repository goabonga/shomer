# feat(admin): CRUD OAuth2 clients API (/admin/clients)

## Description

Admin API for OAuth2 client management: list, get by ID, create, update, delete, rotate secret.

## Objective

Allow administrators to manage OAuth2 client registrations.

## Tasks

- [ ] GET `/admin/clients` — list with pagination
- [ ] GET `/admin/clients/{id}` — client details
- [ ] POST `/admin/clients` — create client (auto-generate client_id/secret)
- [ ] PUT `/admin/clients/{id}` — update client settings
- [ ] DELETE `/admin/clients/{id}` — delete client
- [ ] POST `/admin/clients/{id}/rotate-secret` — rotate client secret
- [ ] RBAC protection
- [ ] Integration tests

## Dependencies

- #27 — OAuth2Client model
- #28 — client service
- #73 — RBAC middleware

## Labels

`feature:admin`, `rfc:6749`, `type:route`, `layer:api`, `size:L`

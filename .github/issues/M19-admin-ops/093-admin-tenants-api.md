# feat(admin): tenants API (/admin/tenants) + members, branding, IdP

## Description

Admin API for tenant management: CRUD tenants, manage members, configure branding, manage identity providers. Comprehensive tenant administration.

## Objective

Provide full tenant administration capabilities for super-admins.

## Tasks

- [ ] GET/POST `/admin/tenants` — list and create tenants
- [ ] GET/PUT/DELETE `/admin/tenants/{id}` — view, update, delete tenant
- [ ] GET/POST/DELETE `/admin/tenants/{id}/members` — manage members
- [ ] PUT `/admin/tenants/{id}/branding` — update branding
- [ ] GET/POST/PUT/DELETE `/admin/tenants/{id}/idps` — manage identity providers
- [ ] GET/PUT `/admin/tenants/{id}/domains` — manage custom domains
- [ ] RBAC protection (super-admin scope)
- [ ] Integration tests

## Dependencies

- #79 — Tenant model
- #73 — RBAC middleware

## Labels

`feature:admin`, `feature:tenant`, `type:route`, `layer:api`, `size:XL`

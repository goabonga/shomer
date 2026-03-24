# feat(admin): [UI] admin sessions, JWKS, roles, scopes, PATs, tenants pages

## Description

Jinja2/HTMX admin pages for managing sessions, JWKS keys, roles, scopes, PATs, and tenants. Comprehensive admin panel for all remaining entities.

## Objective

Complete the admin UI with pages for all manageable entities.

## Tasks

- [ ] Sessions list page with revoke actions
- [ ] JWKS keys page with rotation and revoke actions
- [ ] Roles management page (CRUD, scope assignment)
- [ ] Scopes management page (CRUD)
- [ ] PATs oversight page (list, revoke)
- [ ] Tenants management page (CRUD, members, branding, IdP, domains)
- [ ] Consistent navigation and styling across all admin pages

## Dependencies

- #90 — admin sessions API
- #91 — admin JWKS API
- #92 — admin roles/scopes API
- #93 — admin tenants API
- #94 — admin PATs API

## Labels

`feature:admin`, `layer:ui`, `size:XL`

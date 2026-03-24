## feat(admin): tenants API (/admin/tenants) + members, branding, IdP

## Summary

Admin API for tenant management: CRUD tenants, manage members, configure branding, manage identity providers. Comprehensive tenant administration.

## Changes

- [ ] GET/POST `/admin/tenants` - list and create tenants
- [ ] GET/PUT/DELETE `/admin/tenants/{id}` - view, update, delete tenant
- [ ] GET/POST/DELETE `/admin/tenants/{id}/members` - manage members
- [ ] PUT `/admin/tenants/{id}/branding` - update branding
- [ ] GET/POST/PUT/DELETE `/admin/tenants/{id}/idps` - manage identity providers
- [ ] GET/PUT `/admin/tenants/{id}/domains` - manage custom domains
- [ ] RBAC protection (super-admin scope)
- [ ] Integration tests

## Dependencies

- #79 - Tenant model
- #73 - RBAC middleware

## Related Issue

Closes #93

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



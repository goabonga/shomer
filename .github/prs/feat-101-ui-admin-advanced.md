## feat(admin): [UI] admin sessions, JWKS, roles, scopes, PATs, tenants pages

## Summary

Jinja2/HTMX admin pages for managing sessions, JWKS keys, roles, scopes, PATs, and tenants. Comprehensive admin panel for all remaining entities.

## Changes

- [ ] Sessions list page with revoke actions
- [ ] JWKS keys page with rotation and revoke actions
- [ ] Roles management page (CRUD, scope assignment)
- [ ] Scopes management page (CRUD)
- [ ] PATs oversight page (list, revoke)
- [ ] Tenants management page (CRUD, members, branding, IdP, domains)
- [ ] Consistent navigation and styling across all admin pages

## Dependencies

- #90 - admin sessions API
- #91 - admin JWKS API
- #92 - admin roles/scopes API
- #93 - admin tenants API
- #94 - admin PATs API

## Related Issue

Closes #101

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



## docs(rbac): RBAC and access control guide

## Summary

Guide covering role-based access control: system roles, custom roles, scopes, scope wildcards, role assignment, and how RBAC protects routes.

## Changes

- [ ] RBAC model overview (roles, scopes, assignments)
- [ ] System roles reference (super_admin, admin, user_manager, etc.)
- [ ] Scope naming convention and wildcard matching
- [ ] Creating custom roles and scopes
- [ ] Assigning roles to users (global and per-tenant)
- [ ] Role expiration
- [ ] How RBAC middleware protects routes
- [ ] Examples: restricting API access by role

## Dependencies

- #71–#73 - RBAC implementation

## Related Issue

Closes #120

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



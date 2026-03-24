## feat(admin): sessions API (/admin/sessions)

## Summary

Admin API for session management: list active sessions (with filters by user, tenant), view session details, revoke sessions.

## Changes

- [ ] GET `/admin/sessions` - list with filters (user_id, tenant_id)
- [ ] GET `/admin/sessions/{id}` - session details
- [ ] DELETE `/admin/sessions/{id}` - revoke session
- [ ] DELETE `/admin/users/{id}/sessions` - revoke all sessions for a user
- [ ] RBAC protection
- [ ] Integration tests

## Dependencies

- #6 - Session model
- #73 - RBAC middleware

## Related Issue

Closes #90

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



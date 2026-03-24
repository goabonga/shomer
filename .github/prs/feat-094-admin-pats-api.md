## feat(admin): PATs API (/admin/pats)

## Summary

Admin API for PAT oversight: list all PATs (across users), view details, revoke any PAT.

## Changes

- [ ] GET `/admin/pats` - list all PATs with filters (user_id, scope)
- [ ] GET `/admin/pats/{id}` - PAT details
- [ ] DELETE `/admin/pats/{id}` - revoke PAT
- [ ] RBAC protection
- [ ] Integration tests

## Dependencies

- #74 - PAT model
- #73 - RBAC middleware

## Related Issue

Closes #94

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



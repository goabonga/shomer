## feat(pat): PAT API (POST create, GET list, DELETE revoke)

## Summary

API endpoints for PAT management: POST to create (returns token once), GET to list user's PATs (metadata only), DELETE to revoke.

## Changes

- [ ] POST `/api/pats` - create PAT (name, scopes, expires_at), return token value
- [ ] GET `/api/pats` - list user's PATs (name, prefix, scopes, created_at, last_used_at, expires_at)
- [ ] DELETE `/api/pats/{id}` - revoke PAT
- [ ] Requires authenticated session
- [ ] Integration tests

## Dependencies

- #75 - PAT service
- #20 - session service

## Related Issue

Closes #76

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



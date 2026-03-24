## feat(auth): POST /auth/logout

## Summary

Logout endpoint. Deletes current session, clears cookies. Optional `logout_all` parameter to invalidate all user sessions.

## Changes

- [ ] POST `/auth/logout` route
- [ ] Current session deletion
- [ ] Cookie clearing
- [ ] `logout_all` option to invalidate all sessions
- [ ] Integration test

## Dependencies

- #20 - session service

## Related Issue

Closes #22

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



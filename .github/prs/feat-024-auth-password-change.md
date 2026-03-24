## feat(auth): POST /auth/password/change

## Summary

Password change endpoint for authenticated users. Verifies current password before updating.

## Changes

- [ ] POST `/auth/password/change` route
- [ ] Current password verification
- [ ] New password Argon2id hashing
- [ ] Integration test

## Dependencies

- #19 - login endpoint
- #20 - session service

## Related Issue

Closes #24

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



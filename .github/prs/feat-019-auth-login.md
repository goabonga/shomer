## feat(auth): POST /auth/login

## Summary

Login endpoint by email/password. Argon2id verification, verified email check, session creation, secure cookie response.

## Changes

- [ ] POST `/auth/login` route
- [ ] Request/response schemas
- [ ] Argon2id password verification
- [ ] Verified email check
- [ ] Session creation and secure cookie setting
- [ ] Brute-force protection (rate limiting)
- [ ] Integration test

## Dependencies

- #1 - Argon2id module
- #4 - User models

## Related Issue

Closes #19

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



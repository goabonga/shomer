## feat(auth): POST /auth/register

## Summary

User registration endpoint. Validates unique email, hashes password with Argon2id, creates User + UserEmail + UserPassword, sends verification code by email.

## Changes

- [ ] POST `/auth/register` route
- [ ] Request/response schemas (email, password, username)
- [ ] Email uniqueness check
- [ ] Argon2id password hashing
- [ ] VerificationCode generation and email dispatch
- [ ] Error handling (duplicate email, weak password)
- [ ] Integration test

## Dependencies

- #1 - Argon2id module
- #4 - User models
- #7 - VerificationCode model
- #10 - email service

## Related Issue

Closes #17

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



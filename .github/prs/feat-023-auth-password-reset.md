## feat(auth): POST /auth/password/reset + /reset-verify

## Summary

Forgot password flow: sends a reset token by email, then verifies the token and sets the new password.

## Changes

- [ ] POST `/auth/password/reset` route (sends email with token)
- [ ] POST `/auth/password/reset-verify` route (validates token + sets new password)
- [ ] Token expiration check
- [ ] Single-use enforcement
- [ ] Integration tests

## Dependencies

- #1 - Argon2id module
- #7 - PasswordResetToken model
- #10 - email service

## Related Issue

Closes #23

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



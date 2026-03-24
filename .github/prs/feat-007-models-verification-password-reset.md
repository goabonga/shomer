## feat(models): VerificationCode and PasswordResetToken

## Summary

Models for email verification (6-digit code with expiration) and password reset (UUID token, expiration, single-use flag).

## Changes

- [ ] VerificationCode model (code, email, expires_at, used)
- [ ] PasswordResetToken model (token UUID, user_id, expires_at, used)
- [ ] Alembic migration

## Dependencies

- #4 - User model

## Related Issue

Closes #7

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



## feat(models): UserMFA, MFABackupCode, MFAEmailCode

## Summary

MFA models: UserMFA (encrypted TOTP secret, enabled flag, active methods), MFABackupCode (hashed codes, single-use), MFAEmailCode (6-digit code with expiration for email fallback).

## Changes

- [ ] UserMFA model (totp_secret encrypted, enabled, methods)
- [ ] MFABackupCode model (code_hash, used, user_id)
- [ ] MFAEmailCode model (code, email, expires_at, used)
- [ ] Relationships to User
- [ ] Alembic migration

## Dependencies

- #4 - User model

## Related Issue

Closes #64

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



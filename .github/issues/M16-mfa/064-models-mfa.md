# feat(models): UserMFA, MFABackupCode, MFAEmailCode

## Description

MFA models: UserMFA (encrypted TOTP secret, enabled flag, active methods), MFABackupCode (hashed codes, single-use), MFAEmailCode (6-digit code with expiration for email fallback).

## Objective

Persist all MFA-related state needed for TOTP, backup codes, and email fallback.

## Tasks

- [ ] UserMFA model (totp_secret encrypted, enabled, methods)
- [ ] MFABackupCode model (code_hash, used, user_id)
- [ ] MFAEmailCode model (code, email, expires_at, used)
- [ ] Relationships to User
- [ ] Alembic migration

## Dependencies

- #4 — User model

## Labels

`feature:mfa`, `type:model`, `size:M`

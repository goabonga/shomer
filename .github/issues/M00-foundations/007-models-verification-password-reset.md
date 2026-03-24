# feat(models): VerificationCode and PasswordResetToken

## Description

Models for email verification (6-digit code with expiration) and password reset (UUID token, expiration, single-use flag).

## Objective

Support email verification and password reset flows with dedicated, auditable models.

## Tasks

- [ ] VerificationCode model (code, email, expires_at, used)
- [ ] PasswordResetToken model (token UUID, user_id, expires_at, used)
- [ ] Alembic migration

## Dependencies

- #4 — User model

## Labels

`feature:auth`, `type:model`, `size:S`

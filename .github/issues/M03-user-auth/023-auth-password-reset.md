# feat(auth): POST /auth/password/reset + /reset-verify

## Description

Forgot password flow: sends a reset token by email, then verifies the token and sets the new password.

## Objective

Allow users who forgot their password to securely reset it via email.

## Tasks

- [ ] POST `/auth/password/reset` route (sends email with token)
- [ ] POST `/auth/password/reset-verify` route (validates token + sets new password)
- [ ] Token expiration check
- [ ] Single-use enforcement
- [ ] Integration tests

## Dependencies

- #1 — Argon2id module
- #7 — PasswordResetToken model
- #10 — email service

## Labels

`feature:auth`, `type:route`, `layer:api`, `size:M`

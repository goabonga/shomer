# feat(mfa): MFA verify + email fallback API (verify, email/send, email/verify)

## Description

MFA verification endpoints used during login challenge: POST /mfa/verify (TOTP or backup code), POST /mfa/email/send (send email fallback code), POST /mfa/email/verify (verify email code).

## Objective

Provide the verification endpoints that the login challenge flow calls.

## Tasks

- [ ] POST `/mfa/verify` — verify TOTP code or backup code
- [ ] POST `/mfa/email/send` — send 6-digit code via email
- [ ] POST `/mfa/email/verify` — verify emailed code
- [ ] Rate limiting on email send
- [ ] Integration tests

## Dependencies

- #65 — MFA service

## Labels

`feature:mfa`, `type:route`, `layer:api`, `size:M`

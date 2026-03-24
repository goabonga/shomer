## feat(mfa): MFA verify + email fallback API (verify, email/send, email/verify)

## Summary

MFA verification endpoints used during login challenge: POST /mfa/verify (TOTP or backup code), POST /mfa/email/send (send email fallback code), POST /mfa/email/verify (verify email code).

## Changes

- [ ] POST `/mfa/verify` - verify TOTP code or backup code
- [ ] POST `/mfa/email/send` - send 6-digit code via email
- [ ] POST `/mfa/email/verify` - verify emailed code
- [ ] Rate limiting on email send
- [ ] Integration tests

## Dependencies

- #65 - MFA service

## Related Issue

Closes #67

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



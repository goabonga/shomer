# feat(mfa): MFA setup/management API (status, setup, enable, disable, backup-codes)

## Description

MFA management endpoints: GET /mfa/status, POST /mfa/setup (returns QR + secret), POST /mfa/enable (verifies TOTP code), POST /mfa/disable (verifies code), POST /mfa/backup-codes (regenerate). All require authenticated session.

## Objective

Allow users to set up, enable, disable, and manage their MFA configuration.

## Tasks

- [ ] GET `/mfa/status` — current MFA state
- [ ] POST `/mfa/setup` — generate TOTP secret, return provisioning URI + QR data
- [ ] POST `/mfa/enable` — verify TOTP code to activate MFA
- [ ] POST `/mfa/disable` — verify code to deactivate MFA
- [ ] POST `/mfa/backup-codes` — regenerate backup codes
- [ ] All endpoints require active session
- [ ] Integration tests

## Dependencies

- #20 — session service
- #65 — MFA service

## Labels

`feature:mfa`, `type:route`, `layer:api`, `size:L`

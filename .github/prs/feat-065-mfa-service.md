## feat(mfa): complete MFA service (TOTP, backup codes, email fallback)

## Summary

MFA service: TOTP secret generation + QR code provisioning URI, TOTP code verification (with ±1 period tolerance), backup code generation and verification, email fallback code sending and verification.

## Changes

- [ ] TOTP secret generation (base32 encoded)
- [ ] Provisioning URI for QR code generation
- [ ] TOTP code verification with ±1 period tolerance
- [ ] Backup code generation (set of 10 codes)
- [ ] Backup code verification (single-use, hashed)
- [ ] Email fallback: generate 6-digit code, send via email service, verify
- [ ] Unit tests for each method

## Dependencies

- #1 - encryption for TOTP secret storage
- #10 - email service for fallback codes
- #64 - MFA models

## Related Issue

Closes #65

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



## feat(ui): display otpauth: provisioning URI on MFA setup page

## Summary

- Display the full `otpauth://totp/...` URI on the MFA setup page in a copyable field
- Allows users to copy-paste the URI into CLI TOTP tools or authenticator apps that support URI import

## Changes

- [ ] Add otpauth: URI display in a copyable field on the MFA setup template
- [ ] Unit test for provisioning URI in template context
- [ ] BDD happy path: MFA setup page shows otpauth URI

## Dependencies

- #70 — MFA UI pages

## Related Issue

Closes #261

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present

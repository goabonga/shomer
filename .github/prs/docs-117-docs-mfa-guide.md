## docs(mfa): MFA setup and administration guide

## Summary

Guide covering MFA from both the user and administrator perspective: TOTP setup, backup codes, email fallback, and how MFA interacts with login and OAuth2 flows.

## Changes

- [ ] User guide: TOTP setup with authenticator app
- [ ] User guide: backup codes usage and regeneration
- [ ] User guide: email fallback flow
- [ ] Admin guide: viewing MFA status for users
- [ ] Developer guide: MFA in login flow (two-step challenge)
- [ ] Developer guide: MFA in grant_type=password
- [ ] Screenshots/diagrams of MFA UI flows

## Dependencies

- #64–#70 - MFA implementation

## Related Issue

Closes #117

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



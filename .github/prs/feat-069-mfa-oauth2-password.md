## feat(oauth2): MFA support in grant_type=password

## Summary

Modify the password grant to support MFA: if MFA is enabled, return error=mfa_required with an mfa_token. The client must resend with mfa_token + mfa_code in a second request.

## Changes

- [ ] Check MFA status after password verification in password grant
- [ ] Return error=mfa_required + mfa_token if MFA enabled
- [ ] Accept mfa_token + mfa_code parameters for MFA completion
- [ ] Issue tokens only after MFA verification
- [ ] Integration tests

## Dependencies

- #35 - password grant
- #65 - MFA service

## Related Issue

Closes #69

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



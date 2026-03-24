## feat(auth): POST /auth/verify + POST /auth/verify/resend

## Summary

Email verification by 6-digit code and code resend endpoints. Validates expiration, marks email as verified.

## Changes

- [ ] POST `/auth/verify` route (code validation)
- [ ] POST `/auth/verify/resend` route (new code generation + send)
- [ ] Code expiration check
- [ ] Rate limiting on resend
- [ ] Mark email as verified on success
- [ ] Integration tests

## Dependencies

- #17 - registration endpoint

## Related Issue

Closes #18

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



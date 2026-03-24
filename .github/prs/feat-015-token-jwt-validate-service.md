## feat(token): JWT validation service (signature, claims, expiry)

## Summary

JWT validation service: RS256 signature verification, claims validation (iss, aud, exp), multi-key support via kid lookup in JWKS.

## Changes

- [ ] Signature verification with kid-based key lookup
- [ ] Claims validation (iss, aud, exp, nbf)
- [ ] Clock skew tolerance (configurable)
- [ ] Specific error codes (expired, invalid_signature, invalid_claims)
- [ ] Unit tests

## Dependencies

- #12 - RSA key service

## Related Issue

Closes #15

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



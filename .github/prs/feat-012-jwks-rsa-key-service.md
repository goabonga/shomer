## feat(jwks): RSA key management service (generate, rotate, revoke)

## Summary

RSA key lifecycle management: generation (2048/4096 bits), rotation with grace period (old key stays valid for verification), revocation. Only one active signing key at a time.

## Changes

- [ ] Key generation with configurable RSA size
- [ ] Key rotation: new key becomes active, old key moves to rotated status
- [ ] Grace period: rotated keys remain valid for signature verification
- [ ] Key revocation
- [ ] `get_active_signing_key()` - returns the single active key
- [ ] `get_public_keys()` - returns all non-revoked keys for JWKS
- [ ] Unit tests

## Dependencies

- #11 - JWK model

## Related Issue

Closes #12

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



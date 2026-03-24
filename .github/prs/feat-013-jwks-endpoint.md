## feat(jwks): GET /.well-known/jwks.json

## Summary

Public endpoint returning the JWK Set (active + rotated public keys) in standard RFC 7517 format with appropriate Cache-Control headers.

## Changes

- [ ] GET `/.well-known/jwks.json` route
- [ ] JWK Set JSON serialization (RFC 7517 format)
- [ ] Cache-Control headers
- [ ] Integration test

## Dependencies

- #12 - RSA key service

## Related Issue

Closes #13

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



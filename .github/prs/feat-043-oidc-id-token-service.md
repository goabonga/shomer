## feat(oidc): ID Token generation service (claims, nonce)

## Summary

Dedicated service for generating OIDC ID Tokens. Required claims: iss, sub, aud, exp, iat, nonce, auth_time. Profile claims included based on requested scopes (profile, email, address, phone).

## Changes

- [ ] ID Token generation with required claims
- [ ] Nonce inclusion when provided
- [ ] auth_time claim
- [ ] Profile claims based on scopes (profile → name, email → email, etc.)
- [ ] Unit tests

## Dependencies

- #14 - JWT creation service
- #5 - UserProfile model

## Related Issue

Closes #43

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



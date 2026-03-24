## feat(token): JWT creation service (access_token, id_token)

## Summary

JWT signing service using RS256 for access_token and id_token. Standard claims: iss, sub, aud, exp, iat, jti. Support for scopes and OIDC claims.

## Changes

- [ ] JWT creation with RS256 signing via active JWK
- [ ] Standard claims population (iss, sub, aud, exp, iat, jti)
- [ ] Scope embedding in token claims
- [ ] `kid` header from active signing key
- [ ] Configurable expiration per token type
- [ ] Unit tests

## Dependencies

- #12 - RSA key service

## Related Issue

Closes #14

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



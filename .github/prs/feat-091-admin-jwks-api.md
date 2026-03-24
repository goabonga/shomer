## feat(admin): JWKS API (/admin/jwks)

## Summary

Admin API for JWK management: list keys (with status), view key details, trigger rotation, revoke key.

## Changes

- [ ] GET `/admin/jwks` - list all keys with status
- [ ] GET `/admin/jwks/{kid}` - key details (public key only)
- [ ] POST `/admin/jwks/rotate` - trigger key rotation
- [ ] DELETE `/admin/jwks/{kid}` - revoke key
- [ ] RBAC protection
- [ ] Integration tests

## Dependencies

- #12 - RSA key service
- #73 - RBAC middleware

## Related Issue

Closes #91

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



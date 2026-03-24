## feat(oauth2): POST /oauth2/introspect

## Summary

Token introspection endpoint per RFC 7662. Returns active=true/false with metadata (scope, client_id, username, token_type, exp, iat, sub, aud, iss). Client authentication required.

## Changes

- [ ] POST `/oauth2/introspect` route
- [ ] Client authentication
- [ ] Token lookup and validation
- [ ] Return `active: true` with full metadata for valid tokens
- [ ] Return `active: false` for invalid/expired/revoked tokens
- [ ] token_type_hint support
- [ ] Integration tests

## Dependencies

- #15 - JWT validation
- #33 - token endpoint (shared client auth logic)

## Related Issue

Closes #51

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



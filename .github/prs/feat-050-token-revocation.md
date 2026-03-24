## feat(oauth2): POST /oauth2/revoke

## Summary

Token revocation endpoint per RFC 7009. Supports access_token and refresh_token via token_type_hint. Client authentication required. Returns 200 even if the token is already invalid (no information leakage).

## Changes

- [ ] POST `/oauth2/revoke` route
- [ ] Client authentication
- [ ] token and token_type_hint parameters
- [ ] Revoke access_token (mark as revoked in DB)
- [ ] Revoke refresh_token (mark as revoked, revoke entire family)
- [ ] Always return 200 OK (even for invalid tokens)
- [ ] Integration tests

## Dependencies

- #15 - JWT validation
- #33 - token endpoint (shared client auth logic)

## Related Issue

Closes #50

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



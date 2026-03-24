## feat(oauth2): JAR validation service (JWT request object)

## Summary

Service for validating JWT Request Objects (JAR). Verifies signature (client public key or JWKS), validates claims (iss=client_id, aud=issuer), extracts authorization parameters from the JWT.

## Changes

- [ ] JWT request object parsing
- [ ] Signature verification using client's registered JWKS or jwks_uri
- [ ] Claims validation (iss must equal client_id, aud must equal issuer)
- [ ] Extract authorization parameters from JWT payload
- [ ] Error handling with specific error codes
- [ ] Unit tests

## Dependencies

- #15 - JWT validation service
- #28 - client service

## Related Issue

Closes #60

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



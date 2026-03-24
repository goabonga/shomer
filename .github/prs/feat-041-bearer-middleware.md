## feat(auth): Bearer token extraction middleware

## Summary

FastAPI middleware for extracting Bearer tokens from the Authorization header. Returns 401 with WWW-Authenticate if absent or malformed. Parsing per RFC 6750 §2.1.

## Changes

- [ ] Extract Bearer token from Authorization header
- [ ] Return 401 with `WWW-Authenticate: Bearer` on missing/malformed token
- [ ] Pass extracted token to downstream dependencies
- [ ] Unit tests

## Dependencies

- #15 - JWT validation service

## Related Issue

Closes #41

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



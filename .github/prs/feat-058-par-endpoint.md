## feat(oauth2): POST /oauth2/par

## Summary

PAR endpoint per RFC 9126. Receives authorization parameters via POST, authenticates the client, validates parameters, stores the request, and returns request_uri + expires_in.

## Changes

- [ ] POST `/oauth2/par` route
- [ ] Client authentication
- [ ] Parameter validation (same rules as /authorize)
- [ ] Store PARRequest with generated request_uri
- [ ] Return request_uri + expires_in
- [ ] Integration test

## Dependencies

- #28 - client service
- #57 - PARRequest model

## Related Issue

Closes #58

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



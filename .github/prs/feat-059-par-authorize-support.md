## feat(oauth2): request_uri support in GET /oauth2/authorize

## Summary

Modify /authorize to support the request_uri parameter. Resolves the PARRequest, verifies client_id consistency, uses stored parameters. The request_uri is single-use.

## Changes

- [ ] Detect request_uri parameter in /authorize
- [ ] Lookup PARRequest by request_uri
- [ ] Verify client_id matches
- [ ] Check expiration
- [ ] Use stored parameters (override any query params)
- [ ] Mark request_uri as used (single-use)
- [ ] Integration test

## Dependencies

- #31 - /authorize endpoint
- #58 - PAR endpoint

## Related Issue

Closes #59

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



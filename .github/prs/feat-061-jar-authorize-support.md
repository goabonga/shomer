## feat(oauth2): support "request" param in GET /oauth2/authorize

## Summary

Modify /authorize to support the "request" parameter (JWT). Decodes and validates via the JAR service, merges JWT parameters with query parameters (JWT takes priority).

## Changes

- [ ] Detect "request" parameter in /authorize
- [ ] Validate JWT via JAR service
- [ ] Merge JWT params with query params (JWT wins on conflict)
- [ ] Error response if validation fails
- [ ] Integration test

## Dependencies

- #31 - /authorize endpoint
- #60 - JAR validation service

## Related Issue

Closes #61

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



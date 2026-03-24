## feat(session): sliding session expiration middleware

## Summary

FastAPI middleware for automatic session renewal on each request (sliding expiration). Updates last_activity and extends TTL.

## Changes

- [ ] Middleware implementation
- [ ] Update last_activity timestamp on each request
- [ ] Extend session TTL if within renewal window
- [ ] Skip for unauthenticated requests

## Dependencies

- #20 - session service

## Related Issue

Closes #21

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



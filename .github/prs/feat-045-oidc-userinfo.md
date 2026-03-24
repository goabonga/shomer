## feat(oidc): GET/POST /userinfo

## Summary

OIDC UserInfo endpoint returning user claims based on the scopes of the access token. Supports both GET and POST. Bearer token required.

## Changes

- [ ] GET `/userinfo` route
- [ ] POST `/userinfo` route
- [ ] Bearer token validation
- [ ] Return claims based on token scopes
- [ ] sub claim always included
- [ ] Content-Type: application/json
- [ ] Integration tests

## Dependencies

- #5 - UserProfile model
- #15 - JWT validation
- #42 - get_current_user dependency

## Related Issue

Closes #45

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



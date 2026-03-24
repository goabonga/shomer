## feat(auth): get_current_user dependency (Bearer + session)

## Summary

FastAPI dependency that resolves the current user from either a Bearer JWT token or a session cookie. Bearer takes priority if both are present. Exposes user_id, scopes, and tenant_id.

## Changes

- [ ] Try Bearer token first → validate JWT, extract user_id and scopes
- [ ] Fall back to session cookie → validate session, extract user_id
- [ ] Return 401 if neither is valid
- [ ] Expose user_id, scopes, tenant_id in a CurrentUser object
- [ ] Optional variant (`get_optional_user`) that returns None instead of 401
- [ ] Unit tests

## Dependencies

- #15 - JWT validation service
- #20 - session service
- #41 - Bearer middleware

## Related Issue

Closes #42

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



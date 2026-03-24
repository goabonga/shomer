## feat(rbac): RBAC authorization middleware

## Summary

FastAPI middleware/dependency for route-level authorization. Checks that the current user has the required scope(s) for the requested route. Returns 403 on insufficient permissions.

## Changes

- [ ] `require_scope("scope:name")` dependency
- [ ] `require_any_scope(["scope:a", "scope:b"])` dependency
- [ ] Integration with get_current_user
- [ ] 403 Forbidden response with clear error message
- [ ] Unit tests

## Dependencies

- #72 - permission evaluation service
- #20 - session service (for user context)

## Related Issue

Closes #73

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



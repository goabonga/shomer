## feat(pat): PAT authentication middleware

## Summary

Middleware that authenticates requests using Personal Access Tokens. Integrates with get_current_user so PATs work alongside Bearer JWT and session auth.

## Changes

- [ ] Detect PAT in Authorization header (Bearer shm_pat_...)
- [ ] Validate PAT via PAT service
- [ ] Set current user context with PAT scopes
- [ ] Update last_used_at
- [ ] Integration with get_current_user priority chain
- [ ] Unit tests

## Dependencies

- #75 - PAT service
- #42 - get_current_user dependency

## Related Issue

Closes #77

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



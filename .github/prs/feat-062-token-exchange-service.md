## feat(oauth2): token exchange validation and scope escalation service

## Summary

Token Exchange service: validates the subject_token, checks exchange permissions for the client, computes resulting scopes (intersection or controlled escalation), supports impersonation and delegation.

## Changes

- [ ] Subject token validation (JWT verification)
- [ ] Client permission check for token exchange
- [ ] Scope computation (intersection of requested vs allowed)
- [ ] Impersonation support (act-as)
- [ ] Delegation support (on-behalf-of with actor claim)
- [ ] Unit tests

## Dependencies

- #15 - JWT validation

## Related Issue

Closes #62

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



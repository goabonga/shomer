## feat(profile): GET /api/me

## Summary

First-party endpoint returning the complete profile of the authenticated user: sessions, emails, MFA status, tenant memberships. Distinct from /userinfo (which is OIDC standard).

## Changes

- [ ] GET `/api/me` route
- [ ] Return user profile, emails, MFA status, active sessions count
- [ ] Tenant memberships (if any)
- [ ] Requires session or Bearer authentication
- [ ] Integration test

## Dependencies

- #5 - UserProfile model
- #20 - session service
- #42 - get_current_user dependency

## Related Issue

Closes #46

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



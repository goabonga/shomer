## feat(profile): PUT /api/me/profile + multi-email management

## Summary

Profile update and multi-email management endpoints: PUT /api/me/profile, POST /api/me/emails (add), DELETE /api/me/emails/{id}, PUT /api/me/emails/{id}/primary.

## Changes

- [ ] PUT `/api/me/profile` - update profile fields
- [ ] POST `/api/me/emails` - add a new email (triggers verification)
- [ ] DELETE `/api/me/emails/{id}` - remove a non-primary email
- [ ] PUT `/api/me/emails/{id}/primary` - set email as primary
- [ ] Validation: cannot delete primary email, cannot set unverified as primary
- [ ] Integration tests

## Dependencies

- #5 - UserProfile model
- #46 - GET /api/me
- #10 - email service (for verification)

## Related Issue

Closes #47

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



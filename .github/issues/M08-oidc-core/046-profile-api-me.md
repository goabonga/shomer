# feat(profile): GET /api/me

## Description

First-party endpoint returning the complete profile of the authenticated user: sessions, emails, MFA status, tenant memberships. Distinct from /userinfo (which is OIDC standard).

## Objective

Provide a rich profile endpoint for the application's own frontend.

## Tasks

- [ ] GET `/api/me` route
- [ ] Return user profile, emails, MFA status, active sessions count
- [ ] Tenant memberships (if any)
- [ ] Requires session or Bearer authentication
- [ ] Integration test

## Dependencies

- #5 — UserProfile model
- #20 — session service
- #42 — get_current_user dependency

## Labels

`feature:auth`, `feature:profile`, `type:route`, `layer:api`, `size:M`

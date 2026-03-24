# feat(oidc): GET/POST /userinfo

## Description

OIDC UserInfo endpoint returning user claims based on the scopes of the access token. Supports both GET and POST. Bearer token required.

## Objective

Implement the standard OIDC UserInfo endpoint per OpenID Connect Core 1.0 §5.3.

## Tasks

- [ ] GET `/userinfo` route
- [ ] POST `/userinfo` route
- [ ] Bearer token validation
- [ ] Return claims based on token scopes
- [ ] sub claim always included
- [ ] Content-Type: application/json
- [ ] Integration tests

## Dependencies

- #5 — UserProfile model
- #15 — JWT validation
- #42 — get_current_user dependency

## Labels

`oidc:core`, `feature:profile`, `type:route`, `layer:api`, `size:M`

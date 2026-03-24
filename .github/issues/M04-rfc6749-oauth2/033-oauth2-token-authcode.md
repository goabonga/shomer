# feat(oauth2): POST /oauth2/token — grant_type=authorization_code

## Description

Token endpoint for the authorization_code grant. Client authentication, code validation, PKCE verification, issues access_token + refresh_token + id_token (if scope includes openid).

## Objective

Exchange authorization codes for tokens per RFC 6749 §4.1.3.

## Tasks

- [ ] POST `/oauth2/token` route with grant_type dispatch
- [ ] Client authentication (Basic / POST body)
- [ ] Authorization code validation (exists, not expired, not used, client matches, redirect_uri matches)
- [ ] Mark code as used
- [ ] PKCE code_verifier verification
- [ ] Issue access_token (JWT)
- [ ] Issue refresh_token
- [ ] Issue id_token if scope includes openid
- [ ] Token response format per RFC 6749 §5.1
- [ ] Error responses per RFC 6749 §5.2
- [ ] Integration tests

## Dependencies

- #14 — JWT creation service
- #16 — token models
- #28 — client service
- #29 — AuthorizationCode model

## Labels

`rfc:6749`, `type:route`, `layer:api`, `size:L`

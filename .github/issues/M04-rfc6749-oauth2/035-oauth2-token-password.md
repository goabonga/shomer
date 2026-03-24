# feat(oauth2): POST /oauth2/token — grant_type=password

## Description

Resource Owner Password Credentials grant. Direct authentication by email/password via the token endpoint. Restricted to first-party clients.

## Objective

Support direct login via the token endpoint for trusted clients per RFC 6749 §4.3.

## Tasks

- [ ] grant_type=password handler in token endpoint
- [ ] Client authentication
- [ ] User lookup by email/username and password verification
- [ ] Restrict to clients with password grant enabled
- [ ] Issue access_token + refresh_token
- [ ] Integration test

## Dependencies

- #33 — token endpoint base
- #19 — login logic (password verification)

## Labels

`rfc:6749`, `type:route`, `layer:api`, `size:M`

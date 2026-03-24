# feat(oauth2): POST /oauth2/revoke

## Description

Token revocation endpoint per RFC 7009. Supports access_token and refresh_token via token_type_hint. Client authentication required. Returns 200 even if the token is already invalid (no information leakage).

## Objective

Allow clients to proactively revoke tokens they no longer need.

## Tasks

- [ ] POST `/oauth2/revoke` route
- [ ] Client authentication
- [ ] token and token_type_hint parameters
- [ ] Revoke access_token (mark as revoked in DB)
- [ ] Revoke refresh_token (mark as revoked, revoke entire family)
- [ ] Always return 200 OK (even for invalid tokens)
- [ ] Integration tests

## Dependencies

- #15 — JWT validation
- #33 — token endpoint (shared client auth logic)

## Labels

`rfc:7009`, `type:route`, `layer:api`, `size:M`

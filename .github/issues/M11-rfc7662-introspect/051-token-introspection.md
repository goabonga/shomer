# feat(oauth2): POST /oauth2/introspect

## Description

Token introspection endpoint per RFC 7662. Returns active=true/false with metadata (scope, client_id, username, token_type, exp, iat, sub, aud, iss). Client authentication required.

## Objective

Allow resource servers to validate tokens and retrieve their metadata.

## Tasks

- [ ] POST `/oauth2/introspect` route
- [ ] Client authentication
- [ ] Token lookup and validation
- [ ] Return `active: true` with full metadata for valid tokens
- [ ] Return `active: false` for invalid/expired/revoked tokens
- [ ] token_type_hint support
- [ ] Integration tests

## Dependencies

- #15 — JWT validation
- #33 — token endpoint (shared client auth logic)

## Labels

`rfc:7662`, `type:route`, `layer:api`, `size:L`

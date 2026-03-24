# feat(oauth2): POST /oauth2/token — grant_type=token-exchange

## Description

Token exchange grant (urn:ietf:params:oauth:grant-type:token-exchange) in the token endpoint. Parameters: subject_token, subject_token_type, actor_token (optional), scope, resource, audience. Returns access_token with issued_token_type.

## Objective

Enable secure token exchange between services per RFC 8693.

## Tasks

- [ ] grant_type=urn:ietf:params:oauth:grant-type:token-exchange handler
- [ ] Client authentication
- [ ] Parameter validation (subject_token, subject_token_type required)
- [ ] Delegate to token exchange service
- [ ] Return access_token + issued_token_type
- [ ] Optional refresh_token
- [ ] Integration tests

## Dependencies

- #33 — token endpoint base
- #62 — token exchange service

## Labels

`rfc:8693`, `type:route`, `layer:api`, `size:L`

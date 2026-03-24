# feat(oidc): ID Token generation service (claims, nonce)

## Description

Dedicated service for generating OIDC ID Tokens. Required claims: iss, sub, aud, exp, iat, nonce, auth_time. Profile claims included based on requested scopes (profile, email, address, phone).

## Objective

Centralize ID Token generation with proper OIDC claim handling.

## Tasks

- [ ] ID Token generation with required claims
- [ ] Nonce inclusion when provided
- [ ] auth_time claim
- [ ] Profile claims based on scopes (profile → name, email → email, etc.)
- [ ] Unit tests

## Dependencies

- #14 — JWT creation service
- #5 — UserProfile model

## Labels

`oidc:core`, `type:service`, `size:M`

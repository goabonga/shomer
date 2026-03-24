# feat(jwks): GET /.well-known/jwks.json

## Description

Public endpoint returning the JWK Set (active + rotated public keys) in standard RFC 7517 format with appropriate Cache-Control headers.

## Objective

Allow any relying party to fetch the server's public keys for JWT signature verification.

## Tasks

- [ ] GET `/.well-known/jwks.json` route
- [ ] JWK Set JSON serialization (RFC 7517 format)
- [ ] Cache-Control headers
- [ ] Integration test

## Dependencies

- #12 — RSA key service

## Labels

`rfc:7517`, `type:route`, `layer:api`, `size:S`

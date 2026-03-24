# feat(token): JWT validation service (signature, claims, expiry)

## Description

JWT validation service: RS256 signature verification, claims validation (iss, aud, exp), multi-key support via kid lookup in JWKS.

## Objective

Provide a single validation entry point used by Bearer middleware, introspection, and any token consumer.

## Tasks

- [ ] Signature verification with kid-based key lookup
- [ ] Claims validation (iss, aud, exp, nbf)
- [ ] Clock skew tolerance (configurable)
- [ ] Specific error codes (expired, invalid_signature, invalid_claims)
- [ ] Unit tests

## Dependencies

- #12 — RSA key service

## Labels

`rfc:7519`, `type:service`, `size:M`

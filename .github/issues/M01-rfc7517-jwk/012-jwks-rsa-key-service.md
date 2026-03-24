# feat(jwks): RSA key management service (generate, rotate, revoke)

## Description

RSA key lifecycle management: generation (2048/4096 bits), rotation with grace period (old key stays valid for verification), revocation. Only one active signing key at a time.

## Objective

Manage the full lifecycle of RSA signing keys used for JWT issuance.

## Tasks

- [ ] Key generation with configurable RSA size
- [ ] Key rotation: new key becomes active, old key moves to rotated status
- [ ] Grace period: rotated keys remain valid for signature verification
- [ ] Key revocation
- [ ] `get_active_signing_key()` — returns the single active key
- [ ] `get_public_keys()` — returns all non-revoked keys for JWKS
- [ ] Unit tests

## Dependencies

- #11 — JWK model

## Labels

`rfc:7517`, `rfc:7518`, `feature:jwks`, `type:service`, `size:L`

## feat(jwks): JWK model with encrypted private key

## Summary

JWK model storing kid, algorithm, public key in clear text, and private key encrypted with AES-256-GCM. Supports key statuses: active, rotated, revoked.

## Changes

- [ ] JWK model with status enum (active, rotated, revoked)
- [ ] AES-256-GCM encrypted private key column
- [ ] Public key stored as JWK JSON
- [ ] Indexes on kid and status
- [ ] Alembic migration

## Dependencies

- #1 - AES-256-GCM encryption module
- #3 - declarative base

## Related Issue

Closes #11

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



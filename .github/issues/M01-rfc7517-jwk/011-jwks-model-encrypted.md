# feat(jwks): JWK model with encrypted private key

## Description

JWK model storing kid, algorithm, public key in clear text, and private key encrypted with AES-256-GCM. Supports key statuses: active, rotated, revoked.

## Objective

Persist cryptographic key material securely in the database with full lifecycle tracking.

## Tasks

- [ ] JWK model with status enum (active, rotated, revoked)
- [ ] AES-256-GCM encrypted private key column
- [ ] Public key stored as JWK JSON
- [ ] Indexes on kid and status
- [ ] Alembic migration

## Dependencies

- #1 — AES-256-GCM encryption module
- #3 — declarative base

## Labels

`rfc:7517`, `rfc:7518`, `feature:jwks`, `type:model`, `size:M`

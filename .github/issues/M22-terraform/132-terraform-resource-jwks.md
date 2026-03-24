# feat(terraform): resource shomer_jwk and data source shomer_jwks

## Description

Terraform resource for JWK lifecycle management (generate, rotate, revoke) and data source for reading the current JWKS.

## Objective

Allow key management and JWKS consumption via Terraform.

## Tasks

- [ ] `shomer_jwk` resource: generate key (algorithm, size), read status, trigger rotation, revoke
- [ ] `shomer_jwks` data source: read current public keys (for configuring relying parties)
- [ ] Acceptance tests
- [ ] Documentation with examples

## Dependencies

- #126 — provider scaffold
- #91 — admin JWKS API

## Labels

`feature:admin`, `feature:jwks`, `rfc:7517`, `size:M`

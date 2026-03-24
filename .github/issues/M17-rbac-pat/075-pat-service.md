# feat(pat): PAT service (create, validate, revoke, track usage)

## Description

Personal Access Token service: create (generate token, return plain text once, store hash), validate (lookup by hash, check expiration), revoke, track last_used_at.

## Objective

Provide PAT lifecycle management for API authentication.

## Tasks

- [ ] Create PAT: generate secure random token with `shm_pat_` prefix, hash and store
- [ ] Return plain text token only at creation time
- [ ] Validate PAT: lookup by hash, check expiration and revocation
- [ ] Revoke PAT: mark as revoked
- [ ] Track usage: update last_used_at on each validation
- [ ] List PATs for user (metadata only, no token values)
- [ ] Unit tests

## Dependencies

- #1 — hashing
- #74 — PAT model

## Labels

`feature:pat`, `type:service`, `size:L`

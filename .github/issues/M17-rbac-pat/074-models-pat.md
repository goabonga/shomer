# feat(models): PersonalAccessToken (prefix shm_pat_)

## Description

PersonalAccessToken model with shm_pat_ prefix, hashed token value, name, scopes, expiration, last_used_at tracking.

## Objective

Persist personal access tokens with usage tracking and scoped permissions.

## Tasks

- [ ] PersonalAccessToken model (name, token_prefix, token_hash, scopes, expires_at, last_used_at, user_id)
- [ ] Token prefix: `shm_pat_` for easy identification
- [ ] Index on token_hash for fast lookup
- [ ] Alembic migration

## Dependencies

- #4 — User model

## Labels

`feature:pat`, `type:model`, `size:M`

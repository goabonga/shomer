# feat(models): AccessToken and RefreshToken

## Description

Token storage models. AccessToken (jti, user_id, client_id, scopes, expiry). RefreshToken (token hash, rotation chain, family_id for reuse detection).

## Objective

Enable token lookup, revocation, and refresh token rotation tracking via database-backed models.

## Tasks

- [ ] AccessToken model (jti, user_id, client_id, scopes, expires_at, revoked)
- [ ] RefreshToken model (token_hash, family_id, user_id, client_id, scopes, expires_at, revoked, replaced_by)
- [ ] Indexes on jti, user_id, family_id
- [ ] Alembic migration

## Dependencies

- #3 — declarative base

## Labels

`rfc:6749`, `type:model`, `size:M`

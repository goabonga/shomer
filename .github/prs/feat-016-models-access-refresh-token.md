## feat(models): AccessToken and RefreshToken

## Summary

Token storage models. AccessToken (jti, user_id, client_id, scopes, expiry). RefreshToken (token hash, rotation chain, family_id for reuse detection).

## Changes

- [ ] AccessToken model (jti, user_id, client_id, scopes, expires_at, revoked)
- [ ] RefreshToken model (token_hash, family_id, user_id, client_id, scopes, expires_at, revoked, replaced_by)
- [ ] Indexes on jti, user_id, family_id
- [ ] Alembic migration

## Dependencies

- #3 - declarative base

## Related Issue

Closes #16

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



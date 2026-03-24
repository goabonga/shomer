## feat(models): PersonalAccessToken (prefix shm_pat_)

## Summary

PersonalAccessToken model with shm_pat_ prefix, hashed token value, name, scopes, expiration, last_used_at tracking.

## Changes

- [ ] PersonalAccessToken model (name, token_prefix, token_hash, scopes, expires_at, last_used_at, user_id)
- [ ] Token prefix: `shm_pat_` for easy identification
- [ ] Index on token_hash for fast lookup
- [ ] Alembic migration

## Dependencies

- #4 - User model

## Related Issue

Closes #74

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



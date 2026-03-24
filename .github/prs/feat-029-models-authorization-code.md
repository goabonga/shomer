## feat(models): AuthorizationCode

## Summary

AuthorizationCode model with code, user_id, client_id, redirect_uri, scopes, nonce, code_challenge/method (PKCE), short expiration (10 min), single-use.

## Changes

- [ ] AuthorizationCode model with all fields
- [ ] PKCE fields (code_challenge, code_challenge_method)
- [ ] Single-use flag (used_at timestamp)
- [ ] Short expiration (default 10 minutes)
- [ ] Alembic migration

## Dependencies

- #27 - OAuth2Client model
- #4 - User model

## Related Issue

Closes #29

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



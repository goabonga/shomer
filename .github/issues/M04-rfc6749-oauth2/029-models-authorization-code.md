# feat(models): AuthorizationCode

## Description

AuthorizationCode model with code, user_id, client_id, redirect_uri, scopes, nonce, code_challenge/method (PKCE), short expiration (10 min), single-use.

## Objective

Store authorization codes as the bridge between /authorize and /token.

## Tasks

- [ ] AuthorizationCode model with all fields
- [ ] PKCE fields (code_challenge, code_challenge_method)
- [ ] Single-use flag (used_at timestamp)
- [ ] Short expiration (default 10 minutes)
- [ ] Alembic migration

## Dependencies

- #27 — OAuth2Client model
- #4 — User model

## Labels

`rfc:6749`, `type:model`, `size:S`

# feat(pat): PAT API (POST create, GET list, DELETE revoke)

## Description

API endpoints for PAT management: POST to create (returns token once), GET to list user's PATs (metadata only), DELETE to revoke.

## Objective

Allow users to manage their personal access tokens via API.

## Tasks

- [ ] POST `/api/pats` — create PAT (name, scopes, expires_at), return token value
- [ ] GET `/api/pats` — list user's PATs (name, prefix, scopes, created_at, last_used_at, expires_at)
- [ ] DELETE `/api/pats/{id}` — revoke PAT
- [ ] Requires authenticated session
- [ ] Integration tests

## Dependencies

- #75 — PAT service
- #20 — session service

## Labels

`feature:pat`, `type:route`, `layer:api`, `size:M`

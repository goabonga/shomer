# feat(auth): POST /auth/logout

## Description

Logout endpoint. Deletes current session, clears cookies. Optional `logout_all` parameter to invalidate all user sessions.

## Objective

Allow users to securely end their session(s).

## Tasks

- [ ] POST `/auth/logout` route
- [ ] Current session deletion
- [ ] Cookie clearing
- [ ] `logout_all` option to invalidate all sessions
- [ ] Integration test

## Dependencies

- #20 — session service

## Labels

`feature:auth`, `type:route`, `layer:api`, `size:S`

# feat(auth): POST /auth/login

## Description

Login endpoint by email/password. Argon2id verification, verified email check, session creation, secure cookie response.

## Objective

Authenticate users and establish a browser session.

## Tasks

- [ ] POST `/auth/login` route
- [ ] Request/response schemas
- [ ] Argon2id password verification
- [ ] Verified email check
- [ ] Session creation and secure cookie setting
- [ ] Brute-force protection (rate limiting)
- [ ] Integration test

## Dependencies

- #1 — Argon2id module
- #4 — User models

## Labels

`feature:auth`, `type:route`, `layer:api`, `size:M`

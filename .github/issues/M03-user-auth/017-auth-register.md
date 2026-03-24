# feat(auth): POST /auth/register

## Description

User registration endpoint. Validates unique email, hashes password with Argon2id, creates User + UserEmail + UserPassword, sends verification code by email.

## Objective

Allow new users to create an account with email verification.

## Tasks

- [ ] POST `/auth/register` route
- [ ] Request/response schemas (email, password, username)
- [ ] Email uniqueness check
- [ ] Argon2id password hashing
- [ ] VerificationCode generation and email dispatch
- [ ] Error handling (duplicate email, weak password)
- [ ] Integration test

## Dependencies

- #1 — Argon2id module
- #4 — User models
- #7 — VerificationCode model
- #10 — email service

## Labels

`feature:auth`, `type:route`, `layer:api`, `size:L`

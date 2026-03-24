# feat(auth): POST /auth/password/change

## Description

Password change endpoint for authenticated users. Verifies current password before updating.

## Objective

Allow logged-in users to change their password securely.

## Tasks

- [ ] POST `/auth/password/change` route
- [ ] Current password verification
- [ ] New password Argon2id hashing
- [ ] Integration test

## Dependencies

- #19 — login endpoint
- #20 — session service

## Labels

`feature:auth`, `type:route`, `layer:api`, `size:S`

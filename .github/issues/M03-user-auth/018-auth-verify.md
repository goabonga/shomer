# feat(auth): POST /auth/verify + POST /auth/verify/resend

## Description

Email verification by 6-digit code and code resend endpoints. Validates expiration, marks email as verified.

## Objective

Complete the registration flow by confirming the user owns their email address.

## Tasks

- [ ] POST `/auth/verify` route (code validation)
- [ ] POST `/auth/verify/resend` route (new code generation + send)
- [ ] Code expiration check
- [ ] Rate limiting on resend
- [ ] Mark email as verified on success
- [ ] Integration tests

## Dependencies

- #17 — registration endpoint

## Labels

`feature:auth`, `type:route`, `layer:api`, `size:M`

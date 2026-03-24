# feat(auth): two-step MFA challenge in POST /auth/login

## Description

Modify login to support MFA in two steps: if MFA is enabled, return a temporary mfa_token instead of creating a session. The user must then call /mfa/verify with the mfa_token to complete authentication.

## Objective

Enforce MFA during login without requiring the user to re-enter their password.

## Tasks

- [ ] Check if user has MFA enabled after password verification
- [ ] If MFA enabled: return mfa_token (short-lived JWT) + mfa_required flag
- [ ] Do NOT create session until MFA is verified
- [ ] POST `/mfa/verify` accepts mfa_token, verifies MFA code, creates session
- [ ] mfa_token expiration (5 minutes)
- [ ] Integration tests (login with MFA, login without MFA)

## Dependencies

- #19 — login endpoint
- #65 — MFA service

## Labels

`feature:mfa`, `feature:auth`, `layer:api`, `size:L`

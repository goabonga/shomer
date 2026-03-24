# feat(oauth2): MFA support in grant_type=password

## Description

Modify the password grant to support MFA: if MFA is enabled, return error=mfa_required with an mfa_token. The client must resend with mfa_token + mfa_code in a second request.

## Objective

Enforce MFA in the password grant for first-party clients.

## Tasks

- [ ] Check MFA status after password verification in password grant
- [ ] Return error=mfa_required + mfa_token if MFA enabled
- [ ] Accept mfa_token + mfa_code parameters for MFA completion
- [ ] Issue tokens only after MFA verification
- [ ] Integration tests

## Dependencies

- #35 — password grant
- #65 — MFA service

## Labels

`feature:mfa`, `rfc:6749`, `layer:api`, `size:M`

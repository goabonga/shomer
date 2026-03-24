# feat(oauth2): POST /oauth2/token — grant_type=refresh_token with rotation

## Description

Refresh token grant with mandatory rotation. Each use invalidates the old refresh_token and issues a new one. Reuse detection via family_id triggers revocation of the entire token family.

## Objective

Implement secure refresh token rotation per RFC 6749 §6 with replay detection.

## Tasks

- [ ] grant_type=refresh_token handler in token endpoint
- [ ] Client authentication
- [ ] Refresh token lookup and validation (not expired, not revoked)
- [ ] Mandatory rotation: invalidate old, issue new refresh_token
- [ ] Reuse detection: if already-used token is presented, revoke entire family
- [ ] Issue new access_token
- [ ] Integration tests (happy path + reuse detection)

## Dependencies

- #33 — token endpoint base
- #16 — RefreshToken model (family_id)

## Labels

`rfc:6749`, `type:route`, `layer:api`, `size:M`

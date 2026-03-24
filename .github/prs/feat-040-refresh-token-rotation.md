## feat(oauth2): POST /oauth2/token - grant_type=refresh_token with rotation

## Summary

Refresh token grant with mandatory rotation. Each use invalidates the old refresh_token and issues a new one. Reuse detection via family_id triggers revocation of the entire token family.

## Changes

- [ ] grant_type=refresh_token handler in token endpoint
- [ ] Client authentication
- [ ] Refresh token lookup and validation (not expired, not revoked)
- [ ] Mandatory rotation: invalidate old, issue new refresh_token
- [ ] Reuse detection: if already-used token is presented, revoke entire family
- [ ] Issue new access_token
- [ ] Integration tests (happy path + reuse detection)

## Dependencies

- #33 - token endpoint base
- #16 - RefreshToken model (family_id)

## Related Issue

Closes #40

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



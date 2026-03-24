## feat(oauth2): POST /oauth2/token - grant_type=device_code

## Summary

Device code grant in the token endpoint. Polling with appropriate responses: authorization_pending, slow_down (if interval violated), access_denied, expired_token, or token issuance if approved.

## Changes

- [ ] grant_type=urn:ietf:params:oauth:grant-type:device_code handler
- [ ] Client authentication
- [ ] DeviceCode lookup by device_code
- [ ] Return authorization_pending while pending
- [ ] Return slow_down if polling too fast
- [ ] Return access_denied if denied
- [ ] Return expired_token if expired
- [ ] Issue tokens if approved
- [ ] Integration tests

## Dependencies

- #33 - token endpoint base
- #53 - Device Authorization service

## Related Issue

Closes #55

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



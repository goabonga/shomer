## feat(oauth2): POST /oauth2/device

## Summary

Device Authorization endpoint per RFC 8628. Returns device_code, user_code, verification_uri, verification_uri_complete, expires_in, interval. Client authentication required.

## Changes

- [ ] POST `/oauth2/device` route
- [ ] Client authentication
- [ ] Scope validation
- [ ] Generate device_code and user_code via service
- [ ] Return RFC 8628 §3.2 response format
- [ ] Integration test

## Dependencies

- #53 - Device Authorization service
- #28 - client service

## Related Issue

Closes #54

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



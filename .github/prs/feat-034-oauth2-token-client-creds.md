## feat(oauth2): POST /oauth2/token - grant_type=client_credentials

## Summary

Client credentials grant for machine-to-machine calls. Mandatory client authentication, issues access_token only (no refresh_token, no id_token).

## Changes

- [ ] grant_type=client_credentials handler in token endpoint
- [ ] Client authentication required (confidential clients only)
- [ ] Scope validation against client allowed scopes
- [ ] Issue access_token with client_id as subject
- [ ] No refresh_token or id_token
- [ ] Integration test

## Dependencies

- #33 - token endpoint base

## Related Issue

Closes #34

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



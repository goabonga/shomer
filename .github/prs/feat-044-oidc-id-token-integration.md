## feat(oidc): ID Token integration in POST /oauth2/token (scope openid)

## Summary

Modify the token endpoint to include id_token in the response when scope contains "openid". Applies to authorization_code and refresh_token grants.

## Changes

- [ ] Check for "openid" in granted scopes
- [ ] Generate id_token via ID Token service
- [ ] Include id_token in token response JSON
- [ ] Apply to authorization_code grant
- [ ] Apply to refresh_token grant
- [ ] Integration tests

## Dependencies

- #33 - token endpoint
- #43 - ID Token service

## Related Issue

Closes #44

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



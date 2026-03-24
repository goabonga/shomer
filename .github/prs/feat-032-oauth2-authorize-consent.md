## feat(oauth2): POST /oauth2/authorize - consent

## Summary

Consent processing. Creates AuthorizationCode and redirects to redirect_uri with code and state. Handles denial (error=access_denied).

## Changes

- [ ] POST `/oauth2/authorize` route (consent form submission)
- [ ] CSRF validation
- [ ] AuthorizationCode creation on approval
- [ ] Redirect to redirect_uri with code + state
- [ ] Handle denial → redirect with error=access_denied
- [ ] Integration test

## Dependencies

- #31 - authorization request validation

## Related Issue

Closes #32

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



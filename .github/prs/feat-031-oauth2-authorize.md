## feat(oauth2): GET /oauth2/authorize - request validation

## Summary

OAuth2 authorization endpoint. Validates all parameters (client_id, redirect_uri, response_type, scope, state, nonce), checks user authentication, redirects to login if needed, displays consent screen.

## Changes

- [ ] GET `/oauth2/authorize` route
- [ ] Parameter validation (client_id, redirect_uri, response_type, scope, state)
- [ ] Client lookup and redirect_uri verification
- [ ] Scope validation against client allowed scopes
- [ ] Authentication check - redirect to login with `next` if unauthenticated
- [ ] OIDC parameters support (nonce, prompt, login_hint)
- [ ] Consent check - skip if previously granted
- [ ] Redirect to consent page or auto-approve for first-party clients
- [ ] Error responses per RFC 6749 §4.1.2.1
- [ ] Integration tests

## Dependencies

- #19 - login endpoint
- #20 - session service
- #28 - client service
- #29 - AuthorizationCode model
- #30 - issuer resolver

## Related Issue

Closes #31

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



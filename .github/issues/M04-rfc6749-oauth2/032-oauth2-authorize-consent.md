# feat(oauth2): POST /oauth2/authorize — consent

## Description

Consent processing. Creates AuthorizationCode and redirects to redirect_uri with code and state. Handles denial (error=access_denied).

## Objective

Complete the authorization flow by capturing user consent and issuing the authorization code.

## Tasks

- [ ] POST `/oauth2/authorize` route (consent form submission)
- [ ] CSRF validation
- [ ] AuthorizationCode creation on approval
- [ ] Redirect to redirect_uri with code + state
- [ ] Handle denial → redirect with error=access_denied
- [ ] Integration test

## Dependencies

- #31 — authorization request validation

## Labels

`rfc:6749`, `feature:oauth2`, `type:route`, `layer:api`, `size:M`

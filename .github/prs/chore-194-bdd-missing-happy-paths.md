## test(bdd): add missing happy-path and full-flow BDD scenarios

## Summary

Add happy-path BDD scenarios for all API endpoints and UI pages that currently only have error-case tests.

## Changes

- [ ] POST /auth/login — valid credentials returns 200 + session cookie
- [ ] POST /auth/verify — valid code returns 200 + email verified
- [ ] POST /auth/verify/resend — valid email returns 200 + new code sent
- [ ] POST /auth/password/reset — valid email returns 200
- [ ] POST /auth/password/reset-verify — valid token + new password returns 200
- [ ] POST /auth/password/change — valid session + passwords returns 200
- [ ] GET /oauth2/authorize — valid client redirects to login (302)
- [ ] POST /oauth2/token (authorization_code) — valid code exchange returns access_token
- [ ] POST /oauth2/token (client_credentials) — valid client returns access_token
- [ ] POST /oauth2/token (password) — valid credentials returns access_token + refresh_token
- [ ] UI login form — valid credentials redirects
- [ ] UI verify form — valid code shows success
- [ ] UI verify resend — valid email shows confirmation
- [ ] UI forgot password — valid email shows link sent
- [ ] UI reset password — valid token shows success
- [ ] UI change password — valid session shows success
- [ ] POST /auth/login — unverified email error
- [ ] POST /oauth2/token — unauthorized_client error
- [ ] UI login — unverified email error

## Related Issue

Closes #194

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present

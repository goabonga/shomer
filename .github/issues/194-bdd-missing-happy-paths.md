# test(bdd): add missing happy-path and full-flow BDD scenarios

## Description

Audit shows that many API and UI routes only have error-case BDD tests. Happy paths (valid credentials, successful operations) are missing for 12+ endpoints.

## Tasks

### API happy paths (http_steps.py)

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

### UI happy paths (ui_steps.py / Playwright)

- [ ] Login form — valid credentials redirects
- [ ] Verify form — valid code shows success
- [ ] Verify resend — valid email shows confirmation
- [ ] Forgot password — valid email shows link sent
- [ ] Reset password — valid token shows success
- [ ] Change password — valid session shows success

### Missing error cases

- [ ] POST /auth/login — unverified email error
- [ ] POST /oauth2/token — unauthorized_client error
- [ ] UI login — unverified email error

## Labels

`type:test`, `layer:api`, `layer:ui`

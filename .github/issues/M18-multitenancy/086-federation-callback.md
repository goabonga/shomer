# feat(federation): GET /federation/callback — IdP callback + JIT provisioning + linking

## Description

Federation callback endpoint: receives the authorization code from the external IdP, exchanges it for tokens, extracts user info, performs JIT (Just-In-Time) user provisioning or links to existing account, creates session.

## Objective

Complete the social login / federation flow by handling the IdP callback.

## Tasks

- [ ] GET `/federation/callback` route
- [ ] State parameter validation (CSRF)
- [ ] Authorization code exchange with IdP token endpoint
- [ ] User info extraction from IdP (id_token or userinfo endpoint)
- [ ] Claim mapping per provider configuration
- [ ] JIT provisioning: create user if not exists
- [ ] Account linking: link to existing user by email
- [ ] Create session after successful authentication
- [ ] Error handling (IdP errors, account conflicts)
- [ ] Integration tests

## Dependencies

- #84 — IdentityProvider model
- #17 — user creation logic
- #20 — session service

## Labels

`feature:federation`, `oidc:core`, `type:route`, `layer:api`, `size:L`

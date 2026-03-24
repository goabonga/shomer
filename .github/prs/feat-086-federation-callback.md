## feat(federation): GET /federation/callback — IdP callback + JIT provisioning + linking

## Summary

Federation callback aligned with auth/: handle IdP error responses, decode state, exchange code for tokens, extract user info, JIT provisioning/account linking, create session with cookies, redirect to original URI or fallback. All errors redirect gracefully.

## Changes

### Route handler

- [ ] GET `/federation/callback` (code, state, error, error_description)
- [ ] Handle IdP error → redirect to login with message
- [ ] Decode state (base64 JSON → tenant, idp, nonce, code_verifier, redirect_uri)

### Token exchange and user info

- [ ] Exchange auth code for tokens
- [ ] Extract access_token + id_token
- [ ] Fetch user info + apply attribute mapping

### User provisioning

- [ ] JIT provisioning (create user + email + profile)
- [ ] Account linking by email
- [ ] Add to tenant membership
- [ ] Handle auto_provision disabled

### Session and redirect

- [ ] Create session + set cookies (session_id + csrf_token)
- [ ] Redirect to redirect_uri with preserved state
- [ ] Fallback redirect to /ui/settings/profile

### Error handling

- [ ] ValueError → redirect to login with message
- [ ] Generic exception → redirect with generic error
- [ ] Never 500

### Tests

- [ ] Unit tests for callback handler
- [ ] Unit tests for session creation flow

## Dependencies

- #85 - Federation service
- #84 - IdentityProvider model
- #20 - session service

## Related Issue

Closes #86

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present

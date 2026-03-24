## feat(federation): providers API + federation service + authorize flow

## Summary

Federation providers endpoint and service aligned with auth/: list IdPs for tenant, initiate OAuth2/OIDC authorize flow with PKCE, OIDC discovery fetch, well-known configs for social providers, security helpers, auto-provision.

## Changes

### FederationService

- [ ] `get_tenant_identity_providers()` — list active IdPs
- [ ] `get_identity_provider()` — get single IdP
- [ ] `fetch_oidc_discovery()` — parse `.well-known/openid-configuration`
- [ ] `get_authorization_url()` — build authorize URL with PKCE
- [ ] `exchange_code_for_tokens()` — exchange auth code
- [ ] `get_user_info()` — fetch userinfo from IdP
- [ ] `find_or_create_user()` — auto-provision + link identity
- [ ] `_get_github_user_info()` — GitHub-specific API
- [ ] `_apply_attribute_mapping()` — claim mapping
- [ ] Security helpers: state, nonce, code_verifier, code_challenge

### Data classes

- [ ] OIDCDiscoveryDocument, FederationState, FederatedUserInfo

### Provider configs

- [ ] PROVIDER_CONFIGS for Google, GitHub, Microsoft

### API endpoints

- [ ] GET `/federation/providers` — list with button_text fallback
- [ ] GET `/federation/{idp_id}/authorize` — initiate redirect with PKCE + state

### Tests

- [ ] Unit tests for service + routes
- [ ] BDD happy path

## Dependencies

- #84 - IdentityProvider model
- #80 - tenant resolver middleware

## Related Issue

Closes #85

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present

## feat(models): IdentityProvider and FederatedIdentity

## Summary

Federation models aligned with auth/ project: IdentityProvider (5 provider types, OIDC endpoints, discovery URL, JWKS URI, encrypted client_secret, scopes, attribute mapping, domain restrictions, auto-provision, account linking, UI display settings), FederatedIdentity (user ↔ IdP link with external identity, raw claims, timestamps).

## Changes

### IdentityProvider model

- [ ] IdentityProviderType enum (OIDC, SAML, GOOGLE, GITHUB, MICROSOFT)
- [ ] Core fields: tenant_id, name, provider_type
- [ ] OIDC configuration: discovery_url, authorization_endpoint, token_endpoint, userinfo_endpoint, jwks_uri
- [ ] Client credentials: client_id, client_secret_encrypted (AES-256-GCM)
- [ ] Scopes array (default: openid, profile, email)
- [ ] Attribute mapping JSON (external claim → internal field)
- [ ] Domain restrictions: allowed_domains array
- [ ] Settings: is_active, is_default, auto_provision, allow_linking
- [ ] UI display: icon_url, button_text, display_order
- [ ] Composite index on (tenant_id, is_active)

### FederatedIdentity model

- [ ] Core fields: user_id, identity_provider_id
- [ ] External identity: external_subject, external_email, external_username
- [ ] raw_claims JSON (full IdP response for audit)
- [ ] Timestamps: linked_at, last_login_at
- [ ] Unique constraint on (identity_provider_id, external_subject)
- [ ] Composite index on (user_id, identity_provider_id)

### Relationships and migration

- [ ] Tenant.identity_providers relationship
- [ ] IdentityProvider.federated_identities relationship
- [ ] FederatedIdentity.user and FederatedIdentity.identity_provider
- [ ] Alembic migration
- [ ] Unit tests for both models

## Dependencies

- #79 - Tenant model
- #1 - encryption for client_secret
- #4 - User model

## Related Issue

Closes #84

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present

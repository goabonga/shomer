# feat(models): IdentityProvider and FederatedIdentity

## Description

Federation models: IdentityProvider (type, client_id, client_secret encrypted, endpoints, claim mapping), FederatedIdentity (user_id, provider_id, external_id, profile data).

## Objective

Store external identity provider configuration and linked user identities.

## Tasks

- [ ] IdentityProvider model (name, type enum, client_id, client_secret encrypted, authorization_url, token_url, userinfo_url, claim_mapping JSON, tenant_id)
- [ ] FederatedIdentity model (user_id, provider_id, external_sub, external_email, profile_data JSON)
- [ ] Unique constraint on (provider_id, external_sub)
- [ ] Relationships and indexes
- [ ] Alembic migration

## Dependencies

- #79 — Tenant model
- #1 — encryption for client_secret

## Labels

`feature:federation`, `oidc:core`, `type:model`, `size:M`

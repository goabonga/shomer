# feat(terraform): resource shomer_identity_provider

## Description

Terraform resource for managing identity provider configurations per tenant: Google, GitHub, Microsoft, generic OIDC.

## Objective

Allow federation/social login configuration as code via Terraform.

## Tasks

- [ ] `shomer_identity_provider` resource: create, read, update, delete
- [ ] Attributes: tenant_id, name, type (google/github/microsoft/oidc), client_id, client_secret (sensitive), authorization_url, token_url, userinfo_url, claim_mapping
- [ ] Import support
- [ ] Acceptance tests
- [ ] Documentation with examples (Google, GitHub, generic OIDC)

## Dependencies

- #126 — provider scaffold
- #93 — admin tenants API (IdP sub-resources)

## Labels

`feature:admin`, `feature:federation`, `size:M`

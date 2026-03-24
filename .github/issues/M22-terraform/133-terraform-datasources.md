# feat(terraform): data sources (user, client, role, scope, tenant)

## Description

Terraform data sources for reading existing Shomer resources. Useful for referencing resources managed outside Terraform or for cross-stack references.

## Objective

Enable read-only access to Shomer resources from Terraform configurations.

## Tasks

- [ ] `shomer_user` data source: lookup by ID or email
- [ ] `shomer_oauth2_client` data source: lookup by client_id
- [ ] `shomer_role` data source: lookup by name
- [ ] `shomer_scope` data source: lookup by name
- [ ] `shomer_tenant` data source: lookup by slug
- [ ] Unit tests
- [ ] Documentation

## Dependencies

- #126 — provider scaffold

## Labels

`feature:admin`, `size:M`

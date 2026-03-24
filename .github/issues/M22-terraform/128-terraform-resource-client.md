# feat(terraform): resource shomer_oauth2_client

## Description

Terraform resource for managing OAuth2 clients: create, read, update, delete. Full support for redirect URIs, grant types, scopes, and client type.

## Objective

Allow OAuth2 client registration and configuration via Terraform.

## Tasks

- [ ] `shomer_oauth2_client` resource: create, read, update, delete
- [ ] Attributes: name, client_type (confidential/public), redirect_uris, grant_types, response_types, scopes, logo_uri, tos_uri, policy_uri
- [ ] Computed: client_id, client_secret (sensitive, stored in state)
- [ ] `shomer_oauth2_client_secret_rotation` resource for secret rotation
- [ ] Import support by client_id
- [ ] Acceptance tests
- [ ] Documentation with examples

## Dependencies

- #126 — provider scaffold
- #89 — admin clients API

## Labels

`feature:admin`, `feature:oauth2`, `rfc:6749`, `size:L`

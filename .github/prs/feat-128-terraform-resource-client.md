## feat(terraform): resource shomer_oauth2_client

## Summary

Terraform resource for managing OAuth2 clients: create, read, update, delete. Full support for redirect URIs, grant types, scopes, and client type.

## Changes

- [ ] `shomer_oauth2_client` resource: create, read, update, delete
- [ ] Attributes: name, client_type (confidential/public), redirect_uris, grant_types, response_types, scopes, logo_uri, tos_uri, policy_uri
- [ ] Computed: client_id, client_secret (sensitive, stored in state)
- [ ] `shomer_oauth2_client_secret_rotation` resource for secret rotation
- [ ] Import support by client_id
- [ ] Acceptance tests
- [ ] Documentation with examples

## Dependencies

- #126 - provider scaffold
- #89 - admin clients API

## Related Issue

Closes #128

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



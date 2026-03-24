## feat(terraform): resource shomer_identity_provider

## Summary

Terraform resource for managing identity provider configurations per tenant: Google, GitHub, Microsoft, generic OIDC.

## Changes

- [ ] `shomer_identity_provider` resource: create, read, update, delete
- [ ] Attributes: tenant_id, name, type (google/github/microsoft/oidc), client_id, client_secret (sensitive), authorization_url, token_url, userinfo_url, claim_mapping
- [ ] Import support
- [ ] Acceptance tests
- [ ] Documentation with examples (Google, GitHub, generic OIDC)

## Dependencies

- #126 - provider scaffold
- #93 - admin tenants API (IdP sub-resources)

## Related Issue

Closes #131

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



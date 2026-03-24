## feat(terraform): data sources (user, client, role, scope, tenant)

## Summary

Terraform data sources for reading existing Shomer resources. Useful for referencing resources managed outside Terraform or for cross-stack references.

## Changes

- [ ] `shomer_user` data source: lookup by ID or email
- [ ] `shomer_oauth2_client` data source: lookup by client_id
- [ ] `shomer_role` data source: lookup by name
- [ ] `shomer_scope` data source: lookup by name
- [ ] `shomer_tenant` data source: lookup by slug
- [ ] Unit tests
- [ ] Documentation

## Dependencies

- #126 - provider scaffold

## Related Issue

Closes #133

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



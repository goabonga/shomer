## feat(terraform): resource shomer_tenant and related resources

## Summary

Terraform resources for tenant management: tenant CRUD, member management, branding, custom domains, and identity provider configuration.

## Changes

- [ ] `shomer_tenant` resource: create, read, update, delete (slug, name, settings)
- [ ] `shomer_tenant_member` resource: add/remove member (user_id, role)
- [ ] `shomer_tenant_branding` resource: configure branding (logo_url, colors, favicon, custom_css)
- [ ] `shomer_tenant_domain` resource: add/remove custom domain
- [ ] Import support for all resources
- [ ] Acceptance tests
- [ ] Documentation with examples

## Dependencies

- #126 - provider scaffold
- #93 - admin tenants API

## Related Issue

Closes #130

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



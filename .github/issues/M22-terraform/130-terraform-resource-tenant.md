# feat(terraform): resource shomer_tenant and related resources

## Description

Terraform resources for tenant management: tenant CRUD, member management, branding, custom domains, and identity provider configuration.

## Objective

Allow multi-tenant infrastructure provisioning via Terraform.

## Tasks

- [ ] `shomer_tenant` resource: create, read, update, delete (slug, name, settings)
- [ ] `shomer_tenant_member` resource: add/remove member (user_id, role)
- [ ] `shomer_tenant_branding` resource: configure branding (logo_url, colors, favicon, custom_css)
- [ ] `shomer_tenant_domain` resource: add/remove custom domain
- [ ] Import support for all resources
- [ ] Acceptance tests
- [ ] Documentation with examples

## Dependencies

- #126 — provider scaffold
- #93 — admin tenants API

## Labels

`feature:admin`, `feature:tenant`, `size:XL`

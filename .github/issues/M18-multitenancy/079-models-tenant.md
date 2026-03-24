# feat(models): Tenant, TenantMember, TenantCustomRole

## Description

Multi-tenancy models: Tenant (slug, name, domain, settings), TenantMember (user_id, tenant_id, role), TenantCustomRole (tenant-specific roles beyond system roles).

## Objective

Define the multi-tenancy data model for tenant isolation and membership.

## Tasks

- [ ] Tenant model (slug, name, custom_domain, is_active, settings JSON)
- [ ] TenantMember model (user_id, tenant_id, role, joined_at)
- [ ] TenantCustomRole model (tenant_id, name, permissions)
- [ ] Unique constraints (slug, custom_domain)
- [ ] Relationships and indexes
- [ ] Alembic migration

## Dependencies

- #3 — declarative base
- #4 — User model

## Labels

`feature:tenant`, `type:model`, `size:L`

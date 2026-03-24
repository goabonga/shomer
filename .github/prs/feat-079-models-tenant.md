## feat(models): Tenant, TenantMember, TenantCustomRole

## Summary

Multi-tenancy models: Tenant (slug, name, domain, settings), TenantMember (user_id, tenant_id, role), TenantCustomRole (tenant-specific roles beyond system roles).

## Changes

- [ ] Tenant model (slug, name, custom_domain, is_active, settings JSON)
- [ ] TenantMember model (user_id, tenant_id, role, joined_at)
- [ ] TenantCustomRole model (tenant_id, name, permissions)
- [ ] Unique constraints (slug, custom_domain)
- [ ] Relationships and indexes
- [ ] Alembic migration

## Dependencies

- #3 - declarative base
- #4 - User model

## Related Issue

Closes #79

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



# feat(models): Scope, Role, RoleScope, UserRole

## Description

RBAC models: Scope (name, description), Role (name, description, is_system), RoleScope (many-to-many), UserRole (user_id, role_id, tenant_id, expires_at).

## Objective

Define the authorization model for role-based access control across tenants.

## Tasks

- [ ] Scope model (name with dot notation e.g. "admin:users:read", description)
- [ ] Role model (name, description, is_system flag)
- [ ] RoleScope junction table
- [ ] UserRole model (user_id, role_id, tenant_id, expires_at)
- [ ] Relationships and indexes
- [ ] Alembic migration

## Dependencies

- #3 — declarative base
- #4 — User model

## Labels

`feature:rbac`, `type:model`, `size:L`

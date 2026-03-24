# feat(terraform): resources shomer_role, shomer_scope, shomer_role_scope_assignment

## Description

Terraform resources for RBAC management: roles, scopes, and the assignment of scopes to roles.

## Objective

Allow full RBAC configuration as code via Terraform.

## Tasks

- [ ] `shomer_scope` resource: create, read, delete (name, description)
- [ ] `shomer_role` resource: create, read, update, delete (name, description)
- [ ] `shomer_role_scope_assignment` resource: assign/unassign scope to role
- [ ] `shomer_user_role_assignment` resource: assign/unassign role to user (with optional tenant_id, expires_at)
- [ ] Import support
- [ ] Acceptance tests
- [ ] Documentation with examples

## Dependencies

- #126 — provider scaffold
- #92 — admin roles/scopes API

## Labels

`feature:admin`, `feature:rbac`, `size:L`

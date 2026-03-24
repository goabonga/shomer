# feat(terraform): resource shomer_user

## Description

Terraform resource for managing users: create, read, update, delete. Supports setting active status, roles, and verified email.

## Objective

Allow user provisioning and lifecycle management via Terraform.

## Tasks

- [ ] `shomer_user` resource: create, read, update, delete
- [ ] Attributes: email, username, password, is_active, is_superuser
- [ ] Computed: id, created_at, updated_at
- [ ] Import support by ID or email
- [ ] Acceptance tests
- [ ] Documentation with examples

## Dependencies

- #126 — provider scaffold
- #88 — admin users API

## Labels

`feature:admin`, `feature:auth`, `size:M`

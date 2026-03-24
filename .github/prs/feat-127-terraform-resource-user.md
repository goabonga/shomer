## feat(terraform): resource shomer_user

## Summary

Terraform resource for managing users: create, read, update, delete. Supports setting active status, roles, and verified email.

## Changes

- [ ] `shomer_user` resource: create, read, update, delete
- [ ] Attributes: email, username, password, is_active, is_superuser
- [ ] Computed: id, created_at, updated_at
- [ ] Import support by ID or email
- [ ] Acceptance tests
- [ ] Documentation with examples

## Dependencies

- #126 - provider scaffold
- #88 - admin users API

## Related Issue

Closes #127

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



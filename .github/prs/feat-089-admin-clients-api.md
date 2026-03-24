## feat(admin): CRUD OAuth2 clients API (/admin/clients)

## Summary

Admin API for OAuth2 client management: list, get by ID, create, update, delete, rotate secret.

## Changes

- [ ] GET `/admin/clients` - list with pagination
- [ ] GET `/admin/clients/{id}` - client details
- [ ] POST `/admin/clients` - create client (auto-generate client_id/secret)
- [ ] PUT `/admin/clients/{id}` - update client settings
- [ ] DELETE `/admin/clients/{id}` - delete client
- [ ] POST `/admin/clients/{id}/rotate-secret` - rotate client secret
- [ ] RBAC protection
- [ ] Integration tests

## Dependencies

- #27 - OAuth2Client model
- #28 - client service
- #73 - RBAC middleware

## Related Issue

Closes #89

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



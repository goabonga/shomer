## feat(models): OAuth2Client

## Summary

OAuth2Client model with client_id, hashed client_secret, redirect_uris, allowed grant_types, response_types, scopes, type (confidential/public), and OIDC metadata (logo_uri, tos_uri, etc.).

## Changes

- [ ] OAuth2Client model with all fields
- [ ] Client type enum (confidential, public)
- [ ] JSON columns for redirect_uris, grant_types, response_types, scopes
- [ ] OIDC metadata fields (logo_uri, tos_uri, policy_uri, contacts)
- [ ] Alembic migration

## Dependencies

- #3 - declarative base

## Related Issue

Closes #27

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



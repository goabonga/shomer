## feat(models): PARRequest

## Summary

PARRequest model storing request_uri (urn:ietf:params:oauth:request_uri:xxx), all authorization request parameters, client_id, and short expiration (60s default).

## Changes

- [ ] PARRequest model with request_uri, client_id, parameters JSON, expires_at
- [ ] Unique constraint on request_uri
- [ ] Short default TTL (60 seconds)
- [ ] Alembic migration

## Dependencies

- #27 - OAuth2Client model

## Related Issue

Closes #57

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



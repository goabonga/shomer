## feat(models): DeviceCode

## Summary

DeviceCode model with device_code, user_code (8 chars, human-friendly), client_id, scopes, verification_uri, polling interval, status (pending/approved/denied/expired), user_id (null until approved).

## Changes

- [ ] DeviceCode model with status enum (pending, approved, denied, expired)
- [ ] user_code with human-friendly format (e.g., ABCD-EFGH)
- [ ] Unique constraints on device_code and user_code
- [ ] Expiration field (default 15 minutes)
- [ ] Alembic migration

## Dependencies

- #27 - OAuth2Client model

## Related Issue

Closes #52

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



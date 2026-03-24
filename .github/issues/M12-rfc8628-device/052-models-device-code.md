# feat(models): DeviceCode

## Description

DeviceCode model with device_code, user_code (8 chars, human-friendly), client_id, scopes, verification_uri, polling interval, status (pending/approved/denied/expired), user_id (null until approved).

## Objective

Persist device authorization requests for the device flow lifecycle.

## Tasks

- [ ] DeviceCode model with status enum (pending, approved, denied, expired)
- [ ] user_code with human-friendly format (e.g., ABCD-EFGH)
- [ ] Unique constraints on device_code and user_code
- [ ] Expiration field (default 15 minutes)
- [ ] Alembic migration

## Dependencies

- #27 — OAuth2Client model

## Labels

`rfc:8628`, `type:model`, `size:M`

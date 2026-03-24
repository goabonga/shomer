## feat(oauth2): Device Authorization service

## Summary

Device Authorization service: generates unique device_code/user_code pairs, manages lifecycle (pending → approved/denied/expired), enforces polling interval, associates user on approval.

## Changes

- [ ] Generate unique device_code (secure random) and user_code (human-friendly)
- [ ] Create DeviceCode record with expiration
- [ ] Approve: associate user_id, set status=approved
- [ ] Deny: set status=denied
- [ ] Check: return current status for polling
- [ ] Enforce polling interval (slow_down if too fast)
- [ ] Expire old codes
- [ ] Unit tests

## Dependencies

- #52 - DeviceCode model

## Related Issue

Closes #53

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



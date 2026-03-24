# feat(oauth2): Device Authorization service

## Description

Device Authorization service: generates unique device_code/user_code pairs, manages lifecycle (pending → approved/denied/expired), enforces polling interval, associates user on approval.

## Objective

Encapsulate all device flow business logic in a testable service.

## Tasks

- [ ] Generate unique device_code (secure random) and user_code (human-friendly)
- [ ] Create DeviceCode record with expiration
- [ ] Approve: associate user_id, set status=approved
- [ ] Deny: set status=denied
- [ ] Check: return current status for polling
- [ ] Enforce polling interval (slow_down if too fast)
- [ ] Expire old codes
- [ ] Unit tests

## Dependencies

- #52 — DeviceCode model

## Labels

`rfc:8628`, `type:service`, `size:L`

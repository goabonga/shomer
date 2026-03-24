# feat(oauth2): POST /oauth2/device

## Description

Device Authorization endpoint per RFC 8628. Returns device_code, user_code, verification_uri, verification_uri_complete, expires_in, interval. Client authentication required.

## Objective

Allow devices to initiate the device authorization flow.

## Tasks

- [ ] POST `/oauth2/device` route
- [ ] Client authentication
- [ ] Scope validation
- [ ] Generate device_code and user_code via service
- [ ] Return RFC 8628 §3.2 response format
- [ ] Integration test

## Dependencies

- #53 — Device Authorization service
- #28 — client service

## Labels

`rfc:8628`, `type:route`, `layer:api`, `size:M`

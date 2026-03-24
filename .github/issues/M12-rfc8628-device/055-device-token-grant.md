# feat(oauth2): POST /oauth2/token — grant_type=device_code

## Description

Device code grant in the token endpoint. Polling with appropriate responses: authorization_pending, slow_down (if interval violated), access_denied, expired_token, or token issuance if approved.

## Objective

Complete the device flow by allowing devices to poll for and receive tokens.

## Tasks

- [ ] grant_type=urn:ietf:params:oauth:grant-type:device_code handler
- [ ] Client authentication
- [ ] DeviceCode lookup by device_code
- [ ] Return authorization_pending while pending
- [ ] Return slow_down if polling too fast
- [ ] Return access_denied if denied
- [ ] Return expired_token if expired
- [ ] Issue tokens if approved
- [ ] Integration tests

## Dependencies

- #33 — token endpoint base
- #53 — Device Authorization service

## Labels

`rfc:8628`, `type:route`, `layer:api`, `size:M`

# feat(oauth2): POST /oauth2/token — grant_type=client_credentials

## Description

Client credentials grant for machine-to-machine calls. Mandatory client authentication, issues access_token only (no refresh_token, no id_token).

## Objective

Support server-to-server authentication without user involvement per RFC 6749 §4.4.

## Tasks

- [ ] grant_type=client_credentials handler in token endpoint
- [ ] Client authentication required (confidential clients only)
- [ ] Scope validation against client allowed scopes
- [ ] Issue access_token with client_id as subject
- [ ] No refresh_token or id_token
- [ ] Integration test

## Dependencies

- #33 — token endpoint base

## Labels

`rfc:6749`, `type:route`, `layer:api`, `size:M`

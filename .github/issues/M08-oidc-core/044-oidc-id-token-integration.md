# feat(oidc): ID Token integration in POST /oauth2/token (scope openid)

## Description

Modify the token endpoint to include id_token in the response when scope contains "openid". Applies to authorization_code and refresh_token grants.

## Objective

Make the token endpoint OIDC-compliant by returning ID Tokens when requested.

## Tasks

- [ ] Check for "openid" in granted scopes
- [ ] Generate id_token via ID Token service
- [ ] Include id_token in token response JSON
- [ ] Apply to authorization_code grant
- [ ] Apply to refresh_token grant
- [ ] Integration tests

## Dependencies

- #33 — token endpoint
- #43 — ID Token service

## Labels

`oidc:core`, `rfc:6749`, `layer:api`, `size:M`

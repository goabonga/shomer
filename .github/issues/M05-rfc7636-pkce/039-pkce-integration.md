# feat(pkce): PKCE integration in /authorize and /token

## Description

Integrate PKCE into the authorization_code flow: store code_challenge in AuthorizationCode at /authorize, verify code_verifier at /token. PKCE required for public clients.

## Objective

Enforce PKCE per RFC 7636 to protect the authorization code exchange.

## Tasks

- [ ] Store code_challenge + code_challenge_method in AuthorizationCode during /authorize
- [ ] Require PKCE for public clients, optional for confidential
- [ ] Verify code_verifier against stored challenge in /token
- [ ] Error response if PKCE verification fails
- [ ] Integration tests

## Dependencies

- #31 — /authorize endpoint
- #33 — /token endpoint
- #38 — PKCE service

## Labels

`rfc:7636`, `rfc:6749`, `layer:api`, `size:M`

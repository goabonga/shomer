# docs(oauth2): OAuth2 authorization flows integration guide

## Description

Step-by-step guide for client developers integrating with Shomer's OAuth2 endpoints. Covers each grant type with sequence diagrams, cURL examples, and common pitfalls.

## Objective

Enable third-party developers to integrate OAuth2 flows without reading the source code.

## Tasks

- [ ] Authorization Code + PKCE flow (with sequence diagram)
- [ ] Client Credentials flow
- [ ] Resource Owner Password Credentials flow
- [ ] Refresh Token rotation flow
- [ ] Device Authorization flow (RFC 8628)
- [ ] Token Exchange flow (RFC 8693)
- [ ] Pushed Authorization Requests (RFC 9126)
- [ ] JWT Authorization Requests (RFC 9101)
- [ ] cURL examples for each flow
- [ ] Common errors and troubleshooting per flow
- [ ] Client registration prerequisites

## Dependencies

- #31, #33, #34, #35, #40, #54, #55, #58, #60, #63 — OAuth2 endpoints

## Labels

`type:docs`, `rfc:6749`, `feature:oauth2`, `size:XL`

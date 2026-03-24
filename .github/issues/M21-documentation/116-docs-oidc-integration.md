# docs(oidc): OpenID Connect integration guide

## Description

Guide for relying parties integrating with Shomer as an OIDC provider. Covers discovery, ID Token validation, UserInfo, and scope-to-claim mapping.

## Objective

Enable OIDC relying parties to integrate with Shomer following standard OIDC practices.

## Tasks

- [ ] Discovery endpoint usage (/.well-known/openid-configuration)
- [ ] JWKS endpoint and key rotation handling
- [ ] ID Token structure and validation steps
- [ ] Scope-to-claim mapping table (openid, profile, email, address, phone)
- [ ] UserInfo endpoint usage (GET/POST)
- [ ] Nonce and state parameter best practices
- [ ] Example integration with popular OIDC libraries (Python, Node.js)
- [ ] Testing with Shomer's discovery endpoint

## Dependencies

- #43, #44, #45, #49 — OIDC endpoints

## Labels

`type:docs`, `oidc:core`, `oidc:discovery`, `size:L`

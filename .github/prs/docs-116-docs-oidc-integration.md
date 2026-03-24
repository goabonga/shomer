## docs(oidc): OpenID Connect integration guide

## Summary

Guide for relying parties integrating with Shomer as an OIDC provider. Covers discovery, ID Token validation, UserInfo, and scope-to-claim mapping.

## Changes

- [ ] Discovery endpoint usage (/.well-known/openid-configuration)
- [ ] JWKS endpoint and key rotation handling
- [ ] ID Token structure and validation steps
- [ ] Scope-to-claim mapping table (openid, profile, email, address, phone)
- [ ] UserInfo endpoint usage (GET/POST)
- [ ] Nonce and state parameter best practices
- [ ] Example integration with popular OIDC libraries (Python, Node.js)
- [ ] Testing with Shomer's discovery endpoint

## Dependencies

- #43, #44, #45, #49 - OIDC endpoints

## Related Issue

Closes #116

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



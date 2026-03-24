## feat(oidc): GET /.well-known/openid-configuration

## Summary

OIDC Discovery endpoint returning the server configuration: issuer, endpoints (authorization, token, userinfo, jwks, revocation, introspection, device_authorization, par), supported scopes, response_types, grant_types, token_endpoint_auth_methods, claims, code_challenge_methods.

## Changes

- [ ] GET `/.well-known/openid-configuration` route
- [ ] Dynamic issuer from tenant context
- [ ] All endpoint URLs
- [ ] Supported scopes, response_types, grant_types
- [ ] Supported token_endpoint_auth_methods
- [ ] Supported code_challenge_methods (S256)
- [ ] Cache-Control headers
- [ ] Integration test

## Dependencies

- #30 - issuer resolver

## Related Issue

Closes #49

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



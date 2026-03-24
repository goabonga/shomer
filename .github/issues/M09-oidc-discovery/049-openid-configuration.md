# feat(oidc): GET /.well-known/openid-configuration

## Description

OIDC Discovery endpoint returning the server configuration: issuer, endpoints (authorization, token, userinfo, jwks, revocation, introspection, device_authorization, par), supported scopes, response_types, grant_types, token_endpoint_auth_methods, claims, code_challenge_methods.

## Objective

Allow clients to auto-discover the server's capabilities per OpenID Connect Discovery 1.0.

## Tasks

- [ ] GET `/.well-known/openid-configuration` route
- [ ] Dynamic issuer from tenant context
- [ ] All endpoint URLs
- [ ] Supported scopes, response_types, grant_types
- [ ] Supported token_endpoint_auth_methods
- [ ] Supported code_challenge_methods (S256)
- [ ] Cache-Control headers
- [ ] Integration test

## Dependencies

- #30 — issuer resolver

## Labels

`oidc:discovery`, `type:route`, `layer:api`, `size:M`

# feat(token): JWT creation service (access_token, id_token)

## Description

JWT signing service using RS256 for access_token and id_token. Standard claims: iss, sub, aud, exp, iat, jti. Support for scopes and OIDC claims.

## Objective

Provide a centralized service for minting signed JWTs that all grant types and token endpoints use.

## Tasks

- [ ] JWT creation with RS256 signing via active JWK
- [ ] Standard claims population (iss, sub, aud, exp, iat, jti)
- [ ] Scope embedding in token claims
- [ ] `kid` header from active signing key
- [ ] Configurable expiration per token type
- [ ] Unit tests

## Dependencies

- #12 — RSA key service

## Labels

`rfc:7519`, `oidc:core`, `type:service`, `size:L`

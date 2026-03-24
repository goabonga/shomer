# feat(admin): JWKS API (/admin/jwks)

## Description

Admin API for JWK management: list keys (with status), view key details, trigger rotation, revoke key.

## Objective

Allow administrators to manage the server's signing keys.

## Tasks

- [ ] GET `/admin/jwks` — list all keys with status
- [ ] GET `/admin/jwks/{kid}` — key details (public key only)
- [ ] POST `/admin/jwks/rotate` — trigger key rotation
- [ ] DELETE `/admin/jwks/{kid}` — revoke key
- [ ] RBAC protection
- [ ] Integration tests

## Dependencies

- #12 — RSA key service
- #73 — RBAC middleware

## Labels

`feature:admin`, `rfc:7517`, `type:route`, `layer:api`, `size:M`

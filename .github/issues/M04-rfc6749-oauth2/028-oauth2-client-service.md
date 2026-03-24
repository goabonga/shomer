# feat(oauth2): OAuth2 client management service

## Description

CRUD service for OAuth2 clients: creation with client_id/secret generation, redirect_uri validation, client authentication per RFC 6749 §2.3 and OIDC Core §9, secret rotation.

## Objective

Centralize all client management logic used by admin APIs and the token endpoint.

## RFC 6749 §2.3 — Client Authentication Methods

| Method | Spec | Description | Scope |
|--------|------|-------------|-------|
| `client_secret_basic` | RFC 6749 §2.3.1 | HTTP Basic header (MUST support) | This issue |
| `client_secret_post` | RFC 6749 §2.3.1 | client_id + client_secret in POST body | This issue |
| `none` | RFC 6749 §2.1 / OIDC Core §9 | Public client, no secret (client_id only) | This issue |
| `client_secret_jwt` | OIDC Core §9 / RFC 7523 | HMAC-signed JWT assertion | Future (M8+) |
| `private_key_jwt` | OIDC Core §9 / RFC 7523 | RSA/EC-signed JWT assertion | Future (M8+) |
| `tls_client_auth` | RFC 8705 §2.1 | mTLS with PKI certificate | Future (M18+) |

## Tasks

- [ ] Client creation with random client_id and hashed client_secret (Argon2id)
- [ ] Client lookup by client_id
- [ ] `client_secret_basic` authentication (RFC 6749 §2.3.1 — HTTP Basic, MUST support)
- [ ] `client_secret_post` authentication (RFC 6749 §2.3.1 — POST body)
- [ ] `none` authentication (public clients — client_id only, no secret)
- [ ] `token_endpoint_auth_method` field on OAuth2Client model
- [ ] Redirect URI validation (exact match, no fragments, no wildcards per RFC 6749 §3.1.2.2)
- [ ] Secret rotation (generate new, invalidate old)
- [ ] Unit tests

## Dependencies

- #1 — Argon2id for secret hashing
- #27 — OAuth2Client model

## Labels

`rfc:6749`, `feature:oauth2`, `type:service`, `size:L`

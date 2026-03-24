# feat(pkce): PKCE service (code_challenge S256/plain)

## Description

PKCE service: code_verifier generation, code_challenge computation (S256 and plain), verification of code_verifier against stored code_challenge. S256 required for public clients.

## Objective

Provide PKCE utilities as a standalone service that /authorize and /token integrate with.

## Tasks

- [ ] `generate_code_verifier()` — random 43-128 char string
- [ ] `compute_code_challenge(verifier, method)` — S256 (SHA-256 + base64url) and plain
- [ ] `verify_code_challenge(verifier, challenge, method)` — verification
- [ ] Unit tests

## Dependencies

None.

## Labels

`rfc:7636`, `type:service`, `size:S`

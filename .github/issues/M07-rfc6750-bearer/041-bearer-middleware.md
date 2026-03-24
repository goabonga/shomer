# feat(auth): Bearer token extraction middleware

## Description

FastAPI middleware for extracting Bearer tokens from the Authorization header. Returns 401 with WWW-Authenticate if absent or malformed. Parsing per RFC 6750 §2.1.

## Objective

Provide a reusable middleware that any protected route can depend on for Bearer token extraction.

## Tasks

- [ ] Extract Bearer token from Authorization header
- [ ] Return 401 with `WWW-Authenticate: Bearer` on missing/malformed token
- [ ] Pass extracted token to downstream dependencies
- [ ] Unit tests

## Dependencies

- #15 — JWT validation service

## Labels

`rfc:6750`, `type:infra`, `size:S`

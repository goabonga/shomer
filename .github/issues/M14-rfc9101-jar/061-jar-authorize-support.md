# feat(oauth2): support "request" param in GET /oauth2/authorize

## Description

Modify /authorize to support the "request" parameter (JWT). Decodes and validates via the JAR service, merges JWT parameters with query parameters (JWT takes priority).

## Objective

Allow clients to submit signed authorization requests per RFC 9101.

## Tasks

- [ ] Detect "request" parameter in /authorize
- [ ] Validate JWT via JAR service
- [ ] Merge JWT params with query params (JWT wins on conflict)
- [ ] Error response if validation fails
- [ ] Integration test

## Dependencies

- #31 — /authorize endpoint
- #60 — JAR validation service

## Labels

`rfc:9101`, `rfc:6749`, `layer:api`, `size:M`

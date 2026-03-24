# feat(oauth2): request_uri support in GET /oauth2/authorize

## Description

Modify /authorize to support the request_uri parameter. Resolves the PARRequest, verifies client_id consistency, uses stored parameters. The request_uri is single-use.

## Objective

Complete the PAR flow by allowing /authorize to consume pushed requests.

## Tasks

- [ ] Detect request_uri parameter in /authorize
- [ ] Lookup PARRequest by request_uri
- [ ] Verify client_id matches
- [ ] Check expiration
- [ ] Use stored parameters (override any query params)
- [ ] Mark request_uri as used (single-use)
- [ ] Integration test

## Dependencies

- #31 — /authorize endpoint
- #58 — PAR endpoint

## Labels

`rfc:9126`, `rfc:6749`, `layer:api`, `size:M`

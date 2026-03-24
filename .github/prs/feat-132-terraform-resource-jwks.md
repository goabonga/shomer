## feat(terraform): resource shomer_jwk and data source shomer_jwks

## Summary

Terraform resource for JWK lifecycle management (generate, rotate, revoke) and data source for reading the current JWKS.

## Changes

- [ ] `shomer_jwk` resource: generate key (algorithm, size), read status, trigger rotation, revoke
- [ ] `shomer_jwks` data source: read current public keys (for configuring relying parties)
- [ ] Acceptance tests
- [ ] Documentation with examples

## Dependencies

- #126 - provider scaffold
- #91 - admin JWKS API

## Related Issue

Closes #132

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



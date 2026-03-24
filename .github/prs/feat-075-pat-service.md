## feat(pat): PAT service (create, validate, revoke, track usage)

## Summary

Personal Access Token service: create (generate token, return plain text once, store hash), validate (lookup by hash, check expiration), revoke, track last_used_at.

## Changes

- [ ] Create PAT: generate secure random token with `shm_pat_` prefix, hash and store
- [ ] Return plain text token only at creation time
- [ ] Validate PAT: lookup by hash, check expiration and revocation
- [ ] Revoke PAT: mark as revoked
- [ ] Track usage: update last_used_at on each validation
- [ ] List PATs for user (metadata only, no token values)
- [ ] Unit tests

## Dependencies

- #1 - hashing
- #74 - PAT model

## Related Issue

Closes #75

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



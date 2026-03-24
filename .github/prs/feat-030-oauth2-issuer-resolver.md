## feat(oauth2): dynamic issuer resolver service

## Summary

Service for resolving the issuer URL based on the current tenant. Provides dynamic base URL for tokens and OIDC discovery.

## Changes

- [ ] Issuer resolution from tenant context
- [ ] Fallback to default issuer when no tenant
- [ ] Used by JWT creation, discovery, and token responses
- [ ] Unit tests

## Dependencies

- #2 - configuration

## Related Issue

Closes #30

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



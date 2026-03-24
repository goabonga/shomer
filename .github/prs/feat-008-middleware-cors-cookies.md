## feat(middleware): CORS and secure cookie policy

## Summary

CORS configuration with dynamic origins (per-tenant) and secure cookie policy (HttpOnly, Secure, SameSite=Lax).

## Changes

- [ ] CORS middleware with configurable allowed origins
- [ ] Dynamic origin resolution per tenant
- [ ] Secure cookie defaults (HttpOnly, Secure, SameSite=Lax)
- [ ] Development mode with relaxed CORS for localhost

## Dependencies

- #2 - configuration

## Related Issue

Closes #8

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



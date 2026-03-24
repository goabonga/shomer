## feat(oauth2): POST /oauth2/token - grant_type=password

## Summary

Resource Owner Password Credentials grant. Direct authentication by email/password via the token endpoint. Restricted to first-party clients.

## Changes

- [ ] grant_type=password handler in token endpoint
- [ ] Client authentication
- [ ] User lookup by email/username and password verification
- [ ] Restrict to clients with password grant enabled
- [ ] Issue access_token + refresh_token
- [ ] Integration test

## Dependencies

- #33 - token endpoint base
- #19 - login logic (password verification)

## Related Issue

Closes #35

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



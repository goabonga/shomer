## feat(pkce): PKCE integration in /authorize and /token

## Summary

Integrate PKCE into the authorization_code flow: store code_challenge in AuthorizationCode at /authorize, verify code_verifier at /token. PKCE required for public clients.

## Changes

- [ ] Store code_challenge + code_challenge_method in AuthorizationCode during /authorize
- [ ] Require PKCE for public clients, optional for confidential
- [ ] Verify code_verifier against stored challenge in /token
- [ ] Error response if PKCE verification fails
- [ ] Integration tests

## Dependencies

- #31 - /authorize endpoint
- #33 - /token endpoint
- #38 - PKCE service

## Related Issue

Closes #39

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



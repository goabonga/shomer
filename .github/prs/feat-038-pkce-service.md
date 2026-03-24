## feat(pkce): PKCE service (code_challenge S256/plain)

## Summary

PKCE service: code_verifier generation, code_challenge computation (S256 and plain), verification of code_verifier against stored code_challenge. S256 required for public clients.

## Changes

- [ ] `generate_code_verifier()` - random 43-128 char string
- [ ] `compute_code_challenge(verifier, method)` - S256 (SHA-256 + base64url) and plain
- [ ] `verify_code_challenge(verifier, challenge, method)` - verification
- [ ] Unit tests

## Dependencies

None.

## Related Issue

Closes #38

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



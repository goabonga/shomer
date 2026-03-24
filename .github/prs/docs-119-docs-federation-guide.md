## docs(federation): identity federation and social login configuration

## Summary

Guide for configuring external identity providers (Google, GitHub, Microsoft, generic OIDC) and social login flows.

## Changes

- [ ] Supported provider types and their specifics
- [ ] Step-by-step: configure Google OAuth2
- [ ] Step-by-step: configure GitHub OAuth2
- [ ] Step-by-step: configure Microsoft/Azure AD
- [ ] Step-by-step: configure generic OIDC provider
- [ ] Claim mapping configuration
- [ ] JIT provisioning and account linking behavior
- [ ] Troubleshooting federation issues (redirect mismatch, claim errors)

## Dependencies

- #84–#87 - federation implementation

## Related Issue

Closes #119

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



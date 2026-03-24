## feat(cli): shomer token - token operations commands

## Summary

CLI commands for token operations: introspect a token, revoke a token, list active tokens for a user or client.

## Changes

- [ ] `shomer token introspect <token>` - display token metadata (active, sub, scopes, exp, client_id)
- [ ] `shomer token revoke <token>` - revoke an access or refresh token
- [ ] `shomer token list --user <id|email>` - list active tokens for a user
- [ ] `shomer token list --client <client_id>` - list active tokens for a client
- [ ] `shomer token revoke-all --user <id|email>` - revoke all tokens for a user
- [ ] Rich table output
- [ ] Unit tests

## Dependencies

- #15 - JWT validation service
- #16 - token models

## Related Issue

Closes #111

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



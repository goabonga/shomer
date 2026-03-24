## feat(cli): shomer session - session management commands

## Summary

CLI commands for session management: list active sessions, view details, revoke individual or all sessions for a user.

## Changes

- [ ] `shomer session list` - list sessions (--user, --tenant, --active-only)
- [ ] `shomer session get <id>` - show session details (user, IP, user-agent, last activity)
- [ ] `shomer session revoke <id>` - revoke a single session
- [ ] `shomer session revoke-all --user <id|email>` - revoke all sessions for a user
- [ ] Rich table output
- [ ] Unit tests

## Dependencies

- #6 - Session model
- #20 - session service

## Related Issue

Closes #106

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



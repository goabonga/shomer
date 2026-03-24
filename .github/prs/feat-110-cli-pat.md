## feat(cli): shomer pat - PAT management commands

## Summary

CLI commands for Personal Access Token management: list PATs across users, view details, and revoke.

## Changes

- [ ] `shomer pat list` - list PATs (--user, --expired, pagination)
- [ ] `shomer pat get <id>` - show PAT details (name, scopes, last used, expiration)
- [ ] `shomer pat revoke <id>` - revoke a PAT
- [ ] `shomer pat create --user <email> --name <name> --scopes <scopes>` - create PAT for a user (display token once)
- [ ] Rich table output
- [ ] Unit tests

## Dependencies

- #74 - PAT model
- #75 - PAT service

## Related Issue

Closes #110

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



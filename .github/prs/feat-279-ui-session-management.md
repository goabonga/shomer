## feat(ui): session management in settings (list, revoke, revoke-all)

## Summary

- Add session list with details (IP, user agent, last activity) to /ui/settings/security
- Add revoke individual session and revoke all other sessions actions

## Changes

- [ ] Session list with IP/UA/last activity
- [ ] Revoke individual session
- [ ] Revoke all other sessions
- [ ] Unit tests
- [ ] BDD tests

## Dependencies

- #20 — session service

## Related Issue

Closes #279

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present

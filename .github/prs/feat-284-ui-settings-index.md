## feat(ui): settings index/dashboard page

## Summary

- Add a settings index page at /ui/settings/ with account status overview
- Display profile completeness, email verification, MFA status, sessions count, PAT count

## Changes

- [ ] GET /ui/settings/ index page
- [ ] Profile completeness indicator
- [ ] Email verification status
- [ ] MFA status summary
- [ ] Active sessions count
- [ ] PAT count
- [ ] Unit tests
- [ ] BDD tests

## Dependencies

- #48 — UI user settings pages

## Related Issue

Closes #284

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present

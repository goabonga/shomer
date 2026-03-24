## feat(ui): connected OAuth applications page in settings

## Summary

- Add new settings page listing OAuth2 applications the user has authorized (via consent)
- Add ability to revoke authorized application access

## Changes

- [ ] Settings nav "Applications" link
- [ ] GET /ui/settings/applications page
- [ ] List authorized apps (name, scopes, authorized date)
- [ ] Revoke app access POST handler
- [ ] Unit tests
- [ ] BDD tests

## Dependencies

- #32 — OAuth2 authorize consent

## Related Issue

Closes #280

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present

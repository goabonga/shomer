## feat(pat): [UI] PAT management page

## Summary

Jinja2/HTMX page for managing personal access tokens: create (name, scopes, expiration), list existing PATs, revoke.

## Changes

- [ ] Create PAT form (name, scope selection, expiration date)
- [ ] Display generated token value (show once, copy button)
- [ ] List existing PATs (name, prefix, scopes, last used, expiration)
- [ ] Revoke button with confirmation
- [ ] Integration with user settings navigation

## Dependencies

- #76 - PAT API

## Related Issue

Closes #78

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



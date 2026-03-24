## feat(profile): [UI] user settings pages

## Summary

Jinja2/HTMX pages for user settings: profile (name, avatar, locale), emails (list, add, verify, set primary), security (password, MFA, active sessions).

## Changes

- [ ] Profile settings page (edit name, avatar, locale, timezone)
- [ ] Email management page (list, add, verify, set primary, delete)
- [ ] Security settings page (change password, MFA status, active sessions list)
- [ ] Navigation between settings sections

## Dependencies

- #46 - GET /api/me
- #47 - profile update API

## Related Issue

Closes #48

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



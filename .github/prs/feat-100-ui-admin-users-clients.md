## feat(admin): [UI] admin users and clients pages

## Summary

Jinja2/HTMX admin pages for user and OAuth2 client management: searchable lists, detail views, create/edit forms.

## Changes

- [ ] Users list page with search and filters
- [ ] User detail page (profile, emails, roles, sessions, MFA status)
- [ ] User create/edit form
- [ ] Clients list page
- [ ] Client detail page (settings, redirect URIs, grants)
- [ ] Client create/edit form
- [ ] Secret rotation UI

## Dependencies

- #88 - admin users API
- #89 - admin clients API

## Related Issue

Closes #100

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



## feat(oauth2): [UI] consent screen

## Summary

Jinja2/HTMX consent page showing the requesting client, requested scopes, and Authorize/Deny buttons. Supports tenant branding.

## Changes

- [ ] Consent page template with client info and scope list
- [ ] Authorize and Deny buttons (POST form)
- [ ] Tenant branding support (logo, colors)
- [ ] Scope descriptions (human-readable)
- [ ] CSRF token in form

## Dependencies

- #32 - consent API

## Related Issue

Closes #36

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



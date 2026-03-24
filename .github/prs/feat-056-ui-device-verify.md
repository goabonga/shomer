## feat(oauth2): [UI] device code verification page

## Summary

Jinja2/HTMX page for user_code entry by the user. Shows the requesting client, scopes, and Authorize/Deny buttons. Accessible via verification_uri.

## Changes

- [ ] User code input page (accessible via verification_uri)
- [ ] Auto-fill user_code if verification_uri_complete is used
- [ ] Display client info and requested scopes
- [ ] Authorize and Deny buttons
- [ ] Success and error states
- [ ] Requires authenticated session (redirect to login if needed)

## Dependencies

- #54 - device authorization endpoint

## Related Issue

Closes #56

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



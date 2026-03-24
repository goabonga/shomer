## feat(federation): [UI] provider selection and callback

## Summary

Jinja2/HTMX UI for social login: provider selection buttons on the login page, callback handling page (loading state while processing).

## Changes

- [ ] Social login buttons on login page (Google, GitHub, etc.)
- [ ] Provider-specific icons and styling
- [ ] Redirect to IdP authorization URL on click
- [ ] Callback landing page (processing state)
- [ ] Error display for failed federation

## Dependencies

- #85 - federation providers API
- #86 - federation callback

## Related Issue

Closes #87

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



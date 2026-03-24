## feat(auth): [UI] registration, verification and login pages

## Summary

Jinja2/HTMX pages for registration (form + ToS), email verification (code input), and login (email/password + post-login redirect).

## Changes

- [ ] Registration page with form validation
- [ ] Email verification page with code input and resend button
- [ ] Login page with redirect support (`next` parameter)
- [ ] Shared layout / base template
- [ ] Error and success state display

## Dependencies

- #17 - registration API
- #18 - verification API
- #19 - login API

## Related Issue

Closes #25

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



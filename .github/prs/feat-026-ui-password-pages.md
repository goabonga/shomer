## feat(auth): [UI] forgot password and password change pages

## Summary

Jinja2/HTMX pages for password reset request, new password form (with token), and password change (authenticated user).

## Changes

- [ ] Forgot password page (email input)
- [ ] Reset password page (token + new password)
- [ ] Password change page (current + new password, authenticated)
- [ ] Success and error states

## Dependencies

- #23 - password reset API
- #24 - password change API

## Related Issue

Closes #26

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



## feat(ui): email management in settings (add, remove, verify, set-primary)

## Summary

- Add full email CRUD to /ui/settings/emails: add email form, remove email, verify email with code, resend verification, set primary email
- Currently the page only displays emails; this adds all management actions

## Changes

- [ ] Add email form + POST handler
- [ ] Remove email button + POST handler
- [ ] Verify email flow (code input)
- [ ] Resend verification
- [ ] Set primary email
- [ ] Unit tests
- [ ] BDD tests

## Dependencies

- #48 — UI user settings pages

## Related Issue

Closes #278

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present

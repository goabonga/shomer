# feat(ui): email management in settings (add, remove, verify, set-primary)

## Description

Add full email CRUD to /ui/settings/emails: add email form, remove email, verify email with code, resend verification, set primary email. Currently only displays emails.

## Objective

Allow users to manage their email addresses (add, remove, verify, set primary) directly from the settings UI, aligning with the auth/ project.

## Tasks

- [ ] Add email form + POST handler
- [ ] Remove email button + POST handler
- [ ] Verify email flow (code input)
- [ ] Resend verification
- [ ] Set primary email
- [ ] Unit tests
- [ ] BDD tests

## Dependencies

- #48 — UI user settings pages

## Labels

`feature:ui`, `layer:ui`, `size:M`

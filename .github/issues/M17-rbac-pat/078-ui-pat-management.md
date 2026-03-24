# feat(pat): [UI] PAT management page

## Description

Jinja2/HTMX page for managing personal access tokens: create (name, scopes, expiration), list existing PATs, revoke.

## Objective

Provide a browser UI for users to manage their PATs in account settings.

## Tasks

- [ ] Create PAT form (name, scope selection, expiration date)
- [ ] Display generated token value (show once, copy button)
- [ ] List existing PATs (name, prefix, scopes, last used, expiration)
- [ ] Revoke button with confirmation
- [ ] Integration with user settings navigation

## Dependencies

- #76 — PAT API

## Labels

`feature:pat`, `layer:ui`, `size:M`

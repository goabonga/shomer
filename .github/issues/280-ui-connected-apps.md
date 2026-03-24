# feat(ui): connected OAuth applications page in settings

## Description

New settings page listing OAuth2 applications the user has authorized (via consent), with ability to revoke access.

## Objective

Allow users to view and revoke OAuth2 applications they have authorized, from a dedicated settings page.

## Tasks

- [ ] Settings nav "Applications" link
- [ ] GET /ui/settings/applications page
- [ ] List authorized apps (name, scopes, authorized date)
- [ ] Revoke app access POST handler
- [ ] Unit tests
- [ ] BDD tests

## Dependencies

- #32 — OAuth2 authorize consent

## Labels

`feature:ui`, `layer:ui`, `size:S`

# feat(ui): session management in settings (list, revoke, revoke-all)

## Description

Add session list with details (IP, user agent, last activity) and revoke actions to /ui/settings/security. Currently only shows a session count.

## Objective

Allow users to view active sessions and revoke individual or all sessions from the settings security page.

## Tasks

- [ ] Session list with IP/UA/last activity
- [ ] Revoke individual session
- [ ] Revoke all other sessions
- [ ] Unit tests
- [ ] BDD tests

## Dependencies

- #20 — session service

## Labels

`feature:ui`, `layer:ui`, `size:S`

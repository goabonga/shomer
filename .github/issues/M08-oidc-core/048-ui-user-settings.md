# feat(profile): [UI] user settings pages

## Description

Jinja2/HTMX pages for user settings: profile (name, avatar, locale), emails (list, add, verify, set primary), security (password, MFA, active sessions).

## Objective

Provide the browser UI for users to manage their account settings.

## Tasks

- [ ] Profile settings page (edit name, avatar, locale, timezone)
- [ ] Email management page (list, add, verify, set primary, delete)
- [ ] Security settings page (change password, MFA status, active sessions list)
- [ ] Navigation between settings sections

## Dependencies

- #46 — GET /api/me
- #47 — profile update API

## Labels

`feature:auth`, `feature:profile`, `layer:ui`, `size:L`

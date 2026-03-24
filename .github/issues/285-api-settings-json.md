# feat(api): JSON API endpoints for user settings operations

## Description

Add JSON API counterparts for all settings operations (profile, emails, sessions, MFA, PATs) to enable programmatic access and SPA/mobile integration.

## Objective

Provide a complete JSON API for all user settings operations, enabling programmatic access from SPAs, mobile apps, and third-party integrations.

## Tasks

- [ ] GET/PUT /api/settings/profile
- [ ] GET/POST/DELETE /api/settings/emails
- [ ] GET/DELETE /api/settings/sessions
- [ ] GET /api/settings/security (MFA status + sessions)
- [ ] Consistent error format
- [ ] Unit tests
- [ ] BDD tests

## Dependencies

- #46 — profile API me
- #47 — profile API update

## Labels

`feature:api`, `layer:api`, `size:L`

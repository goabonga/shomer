## feat(api): JSON API endpoints for user settings operations

## Summary

- Add JSON API counterparts for all settings operations (profile, emails, sessions, MFA, PATs)
- Enable programmatic access and SPA/mobile integration with consistent error format

## Changes

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

## Related Issue

Closes #285

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present

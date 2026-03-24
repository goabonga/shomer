## feat(admin): [UI] dashboard

## Summary

Jinja2/HTMX admin dashboard page displaying system statistics: users, sessions, clients, tokens, MFA adoption, recent activity.

## Changes

- [ ] Dashboard page with stat cards
- [ ] User count and growth chart
- [ ] Active sessions count
- [ ] Recent activity feed
- [ ] Quick action links (create user, create client, etc.)
- [ ] Admin layout with navigation sidebar

## Dependencies

- #95 - dashboard API

## Related Issue

Closes #99

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



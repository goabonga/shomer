## feat(admin): GET /admin/dashboard

## Summary

Admin dashboard endpoint returning aggregate statistics: total users, active sessions, OAuth2 clients count, tokens issued (24h), MFA adoption rate, recent activity.

## Changes

- [ ] GET `/admin/dashboard` route
- [ ] User statistics (total, active, verified)
- [ ] Session statistics (active count)
- [ ] Client statistics (total, by type)
- [ ] Token statistics (issued in last 24h)
- [ ] MFA adoption rate
- [ ] RBAC protection
- [ ] Integration test

## Dependencies

- #73 - RBAC middleware

## Related Issue

Closes #95

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



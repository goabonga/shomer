# feat(admin): GET /admin/dashboard

## Description

Admin dashboard endpoint returning aggregate statistics: total users, active sessions, OAuth2 clients count, tokens issued (24h), MFA adoption rate, recent activity.

## Objective

Give administrators a quick overview of the system state.

## Tasks

- [ ] GET `/admin/dashboard` route
- [ ] User statistics (total, active, verified)
- [ ] Session statistics (active count)
- [ ] Client statistics (total, by type)
- [ ] Token statistics (issued in last 24h)
- [ ] MFA adoption rate
- [ ] RBAC protection
- [ ] Integration test

## Dependencies

- #73 — RBAC middleware

## Labels

`feature:admin`, `type:route`, `layer:api`, `size:M`

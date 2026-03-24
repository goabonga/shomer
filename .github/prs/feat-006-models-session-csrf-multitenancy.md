## feat(models): Session with CSRF and multi-tenancy

## Summary

Session model with CSRF token, multi-tenancy support (tenant_id), user-agent, IP address, last activity timestamp, and sliding expiration.

## Changes

- [ ] Session model (token_hash, csrf_token, user_id, tenant_id, user_agent, ip_address, last_activity, expires_at)
- [ ] Indexes on user_id and tenant_id
- [ ] Alembic migration

## Dependencies

- #4 - User model

## Related Issue

Closes #6

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



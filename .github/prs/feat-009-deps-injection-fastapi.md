## feat(deps): FastAPI dependency injection system

## Summary

FastAPI dependency injection setup for all services: DB session, current user, current tenant, configuration, etc.

## Changes

- [ ] `get_db` async session dependency
- [ ] `get_config` dependency
- [ ] `get_current_tenant` dependency (placeholder, wired in M18)
- [ ] Typing helpers and base patterns for service injection
- [ ] Unit tests validating DI wiring

## Dependencies

- #2 - configuration

## Related Issue

Closes #9

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



# feat(deps): FastAPI dependency injection system

## Description

FastAPI dependency injection setup for all services: DB session, current user, current tenant, configuration, etc.

## Objective

Establish a clean DI pattern so every route handler receives its dependencies through FastAPI's Depends() system.

## Tasks

- [ ] `get_db` async session dependency
- [ ] `get_config` dependency
- [ ] `get_current_tenant` dependency (placeholder, wired in M18)
- [ ] Typing helpers and base patterns for service injection
- [ ] Unit tests validating DI wiring

## Dependencies

- #2 — configuration

## Labels

`type:infra`, `size:M`

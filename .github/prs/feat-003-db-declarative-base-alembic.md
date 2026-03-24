## feat(db): async SQLAlchemy declarative base, TimestampMixin, Alembic

## Summary

Async SQLAlchemy declarative base with TimestampMixin (created_at / updated_at auto-managed), async session factory, and Alembic migration configuration.

## Changes

- [ ] Declarative base with UUID primary key mixin
- [ ] TimestampMixin with server-side defaults
- [ ] Async engine and session factory
- [ ] Alembic configuration with async driver support
- [ ] Initial empty migration to validate setup

## Dependencies

None.

## Related Issue

Closes #3

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



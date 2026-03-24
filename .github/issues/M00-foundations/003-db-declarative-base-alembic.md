# feat(db): async SQLAlchemy declarative base, TimestampMixin, Alembic

## Description

Async SQLAlchemy declarative base with TimestampMixin (created_at / updated_at auto-managed), async session factory, and Alembic migration configuration.

## Objective

Establish the database foundation that every model in the project will inherit from.

## Tasks

- [ ] Declarative base with UUID primary key mixin
- [ ] TimestampMixin with server-side defaults
- [ ] Async engine and session factory
- [ ] Alembic configuration with async driver support
- [ ] Initial empty migration to validate setup

## Dependencies

None.

## Labels

`type:model`, `type:infra`, `size:S`

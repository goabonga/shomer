## docs(database): database schema and migrations guide

## Summary

Guide covering database setup, the Alembic migration workflow, and how to write and manage migrations when extending Shomer.

## Changes

- [ ] Database requirements (PostgreSQL version, extensions)
- [ ] Initial database setup and first migration
- [ ] Alembic commands reference (upgrade, downgrade, revision, autogenerate)
- [ ] Writing a new migration (best practices, naming conventions)
- [ ] Handling migration conflicts
- [ ] Database schema overview with model relationships
- [ ] Backup before migration workflow

## Dependencies

- #3 - database foundation

## Related Issue

Closes #124

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



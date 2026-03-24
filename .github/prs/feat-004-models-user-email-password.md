## feat(models): User, UserEmail and UserPassword

## Summary

Core user models. User with UUID primary key, UserEmail with multi-email support (verified flag, primary flag), UserPassword with Argon2id hash storage.

## Changes

- [ ] User model (id, username, is_active, is_superuser)
- [ ] UserEmail model (email, verified, is_primary, user_id) with unique constraint
- [ ] UserPassword model (password_hash, user_id)
- [ ] SQLAlchemy relationships between models
- [ ] Alembic migration
- [ ] Basic CRUD query helpers

## Dependencies

- #3 - declarative base and Alembic

## Related Issue

Closes #4

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



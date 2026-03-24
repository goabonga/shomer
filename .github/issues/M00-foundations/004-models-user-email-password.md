# feat(models): User, UserEmail and UserPassword

## Description

Core user models. User with UUID primary key, UserEmail with multi-email support (verified flag, primary flag), UserPassword with Argon2id hash storage.

## Objective

Define the canonical user identity models that the entire auth system builds upon.

## Tasks

- [ ] User model (id, username, is_active)
- [ ] UserEmail model (email, verified, is_primary, user_id) with unique constraint
- [ ] UserPassword model (password_hash, user_id)
- [ ] SQLAlchemy relationships between models
- [ ] Alembic migration
- [ ] Basic CRUD query helpers

## Dependencies

- #3 — declarative base and Alembic

## Labels

`feature:auth`, `type:model`, `oidc:core`, `size:M`

# feat(models): UserProfile with standard OIDC claims

## Description

UserProfile model storing standard OIDC claims: name, given_name, family_name, nickname, picture, locale, zoneinfo, birthdate, gender, website, etc.

## Objective

Separate profile data from identity data so OIDC claims can be served from a dedicated model.

## Tasks

- [ ] UserProfile model with all standard OIDC claim fields
- [ ] One-to-one relationship with User
- [ ] Alembic migration

## Dependencies

- #4 — User model

## Labels

`oidc:core`, `feature:profile`, `type:model`, `size:S`

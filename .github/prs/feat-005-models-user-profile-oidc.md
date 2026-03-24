## feat(models): UserProfile with standard OIDC claims

## Summary

UserProfile model storing standard OIDC claims: name, given_name, family_name, nickname, picture, locale, zoneinfo, birthdate, gender, website, etc.

## Changes

- [ ] UserProfile model with all standard OIDC claim fields
- [ ] One-to-one relationship with User
- [ ] Alembic migration

## Dependencies

- #4 - User model

## Related Issue

Closes #5

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



## docs(config): complete configuration reference

## Summary

Exhaustive reference of all configuration settings: environment variables, `.env` file options, systemd-creds secrets, and their defaults, types, and validation rules.

## Changes

- [ ] Table of all environment variables with type, default, description
- [ ] Section: database settings (DATABASE_URL, pool size, etc.)
- [ ] Section: Redis / Celery settings
- [ ] Section: security settings (master key, Argon2id params, JWT expiration)
- [ ] Section: OAuth2 settings (issuer, token lifetimes, PKCE policy)
- [ ] Section: email settings (SMTP, Mailler, templates)
- [ ] Section: multi-tenancy settings
- [ ] Section: systemd-creds usage examples
- [ ] Example `.env` file for development and production

## Dependencies

- #2 - config module must be finalized

## Related Issue

Closes #113

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



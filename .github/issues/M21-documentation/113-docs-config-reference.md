# docs(config): complete configuration reference

## Description

Exhaustive reference of all configuration settings: environment variables, `.env` file options, systemd-creds secrets, and their defaults, types, and validation rules.

## Objective

Provide a single page where operators can find every configurable parameter.

## Tasks

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

- #2 — config module must be finalized

## Labels

`type:docs`, `size:M`

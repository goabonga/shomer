## feat(config): Pydantic settings with file-based secrets support

## Summary

Split monolithic connection URLs into individual components (host, port, user, password) for database and Redis. Passwords loaded via `get_credential()` which reads from `CREDENTIALS_DIRECTORY` (systemd-creds, Vault Agent, K8s mounts) with env var fallback. Docker Compose and Helm chart updated to use secrets.

## Changes

- [x] Pydantic BaseSettings with split connection components (db host/port/user/password/name, redis host/port/db/password)
- [x] `get_credential()` reads secrets from `CREDENTIALS_DIRECTORY` with env var fallback
- [x] Priority chain: env vars > secret files > .env file > defaults
- [x] Unit tests for settings, get_credential, and priority chain
- [x] Docker Compose: use Docker secrets for database and redis passwords
- [x] Helm chart: K8s Secret for passwords, volume mount at `/run/credentials`, `enableServiceLinks: false`
- [ ] Validation rules (URL formats, key lengths, required secrets)

## Dependencies

None.

## Related Issue

Closes #2

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present

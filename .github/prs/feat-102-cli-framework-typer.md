## feat(cli): Typer framework with API client and authentication

## Summary

Set up the CLI framework using Typer with a built-in HTTP client that authenticates against the Shomer admin API. The CLI acts as an administration client - it does not start or manage server processes. Supports base URL configuration, authentication via PAT or credentials, and Rich output formatting.

## Changes

- [ ] Typer app with `shomer --version` and `--help`
- [ ] Configuration file (`~/.shomer/config.toml`) for base URL, default tenant
- [ ] `shomer login` - authenticate and store PAT or session token
- [ ] `shomer logout` - clear stored credentials
- [ ] `shomer status` - check API connectivity and auth status
- [ ] HTTP client wrapper (httpx) with auth header injection
- [ ] `--url` and `--token` global options to override config
- [ ] `--format` option (table, json, yaml) for output
- [ ] Rich console output for tables and errors
- [ ] Error handling (connection refused, 401, 403, 404, 500)
- [ ] Unit tests for CLI invocation and client setup

## Dependencies

None - this is the CLI foundation.

## Related Issue

Closes #102

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



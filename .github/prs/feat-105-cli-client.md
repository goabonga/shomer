## feat(cli): shomer client - OAuth2 client management commands

## Summary

CLI commands for OAuth2 client management: list, view, create, update, delete, and rotate secret.

## Changes

- [ ] `shomer client list` - list clients (with filters: --type, --tenant)
- [ ] `shomer client get <client_id>` - show client details
- [ ] `shomer client create` - create client (--name, --type, --redirect-uris, --grant-types, --scopes)
- [ ] `shomer client update <client_id>` - update client settings
- [ ] `shomer client delete <client_id>` - delete client (with --confirm)
- [ ] `shomer client rotate-secret <client_id>` - rotate client secret (display new secret once)
- [ ] Rich table output
- [ ] Unit tests

## Dependencies

- #27 - OAuth2Client model
- #28 - client service

## Related Issue

Closes #105

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



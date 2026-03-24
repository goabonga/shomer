# feat(cli): shomer client — OAuth2 client management commands

## Description

CLI commands for OAuth2 client management: list, view, create, update, delete, and rotate secret.

## Objective

Enable OAuth2 client management from the command line.

## Tasks

- [ ] `shomer client list` — list clients (with filters: --type, --tenant)
- [ ] `shomer client get <client_id>` — show client details
- [ ] `shomer client create` — create client (--name, --type, --redirect-uris, --grant-types, --scopes)
- [ ] `shomer client update <client_id>` — update client settings
- [ ] `shomer client delete <client_id>` — delete client (with --confirm)
- [ ] `shomer client rotate-secret <client_id>` — rotate client secret (display new secret once)
- [ ] Rich table output
- [ ] Unit tests

## Dependencies

- #27 — OAuth2Client model
- #28 — client service

## Labels

`feature:admin`, `feature:oauth2`, `rfc:6749`, `size:M`

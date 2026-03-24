# feat(cli): shomer token — token operations commands

## Description

CLI commands for token operations: introspect a token, revoke a token, list active tokens for a user or client.

## Objective

Enable token inspection and management from the command line for debugging and administration.

## Tasks

- [ ] `shomer token introspect <token>` — display token metadata (active, sub, scopes, exp, client_id)
- [ ] `shomer token revoke <token>` — revoke an access or refresh token
- [ ] `shomer token list --user <id|email>` — list active tokens for a user
- [ ] `shomer token list --client <client_id>` — list active tokens for a client
- [ ] `shomer token revoke-all --user <id|email>` — revoke all tokens for a user
- [ ] Rich table output
- [ ] Unit tests

## Dependencies

- #15 — JWT validation service
- #16 — token models

## Labels

`feature:admin`, `rfc:7009`, `rfc:7662`, `size:M`

# feat(cli): shomer session — session management commands

## Description

CLI commands for session management: list active sessions, view details, revoke individual or all sessions for a user.

## Objective

Enable session monitoring and revocation from the command line.

## Tasks

- [ ] `shomer session list` — list sessions (--user, --tenant, --active-only)
- [ ] `shomer session get <id>` — show session details (user, IP, user-agent, last activity)
- [ ] `shomer session revoke <id>` — revoke a single session
- [ ] `shomer session revoke-all --user <id|email>` — revoke all sessions for a user
- [ ] Rich table output
- [ ] Unit tests

## Dependencies

- #6 — Session model
- #20 — session service

## Labels

`feature:admin`, `feature:session`, `size:S`

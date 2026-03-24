# feat(cli): shomer pat — PAT management commands

## Description

CLI commands for Personal Access Token management: list PATs across users, view details, and revoke.

## Objective

Enable PAT oversight and revocation from the command line.

## Tasks

- [ ] `shomer pat list` — list PATs (--user, --expired, pagination)
- [ ] `shomer pat get <id>` — show PAT details (name, scopes, last used, expiration)
- [ ] `shomer pat revoke <id>` — revoke a PAT
- [ ] `shomer pat create --user <email> --name <name> --scopes <scopes>` — create PAT for a user (display token once)
- [ ] Rich table output
- [ ] Unit tests

## Dependencies

- #74 — PAT model
- #75 — PAT service

## Labels

`feature:admin`, `feature:pat`, `size:S`

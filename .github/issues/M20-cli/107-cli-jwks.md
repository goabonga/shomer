# feat(cli): shomer jwks — key management commands

## Description

CLI commands for JWK management: list keys, view details, generate new key, rotate, and revoke.

## Objective

Enable cryptographic key lifecycle management from the command line.

## Tasks

- [ ] `shomer jwks list` — list all keys with status (active, rotated, revoked)
- [ ] `shomer jwks get <kid>` — show key details (public key, algorithm, status, created_at)
- [ ] `shomer jwks generate` — generate a new RSA key (--size 2048|4096)
- [ ] `shomer jwks rotate` — rotate the active key (new key becomes active, old moves to rotated)
- [ ] `shomer jwks revoke <kid>` — revoke a key
- [ ] Rich table output
- [ ] Unit tests

## Dependencies

- #11 — JWK model
- #12 — RSA key service

## Labels

`feature:admin`, `feature:jwks`, `rfc:7517`, `size:M`

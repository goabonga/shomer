## feat(cli): shomer jwks - key management commands

## Summary

CLI commands for JWK management: list keys, view details, generate new key, rotate, and revoke.

## Changes

- [ ] `shomer jwks list` - list all keys with status (active, rotated, revoked)
- [ ] `shomer jwks get <kid>` - show key details (public key, algorithm, status, created_at)
- [ ] `shomer jwks generate` - generate a new RSA key (--size 2048|4096)
- [ ] `shomer jwks rotate` - rotate the active key (new key becomes active, old moves to rotated)
- [ ] `shomer jwks revoke <kid>` - revoke a key
- [ ] Rich table output
- [ ] Unit tests

## Dependencies

- #11 - JWK model
- #12 - RSA key service

## Related Issue

Closes #107

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



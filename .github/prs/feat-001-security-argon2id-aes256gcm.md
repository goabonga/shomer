## feat(security): Argon2id hashing and AES-256-GCM encryption module

## Summary

Core security module providing Argon2id password hashing and AES-256-GCM symmetric encryption for private keys and sensitive data. This is the cryptographic foundation of the entire auth server.

## Changes

- [ ] Argon2id hash and verify functions with configurable parameters (memory, iterations, parallelism)
- [ ] AES-256-GCM encrypt/decrypt with key derivation from master secret
- [ ] Constant-time comparison utility
- [ ] Unit tests for hash, verify, encrypt, decrypt
- [ ] Benchmark tests to validate Argon2id timing targets

## Dependencies

None - this is a foundational module.

## Related Issue

Closes #1

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



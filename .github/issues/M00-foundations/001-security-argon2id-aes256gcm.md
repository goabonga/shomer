# feat(security): Argon2id hashing and AES-256-GCM encryption module

## Description

Core security module providing Argon2id password hashing and AES-256-GCM symmetric encryption for private keys and sensitive data. This is the cryptographic foundation of the entire auth server.

## Objective

Provide a single, well-tested security module that all other components rely on for hashing and encryption operations.

## Tasks

- [ ] Argon2id hash and verify functions with configurable parameters (memory, iterations, parallelism)
- [ ] AES-256-GCM encrypt/decrypt with key derivation from master secret
- [ ] Constant-time comparison utility
- [ ] Unit tests for hash, verify, encrypt, decrypt
- [ ] Benchmark tests to validate Argon2id timing targets

## Dependencies

None — this is a foundational module.

## Labels

`feature:auth`, `type:service`, `size:M`

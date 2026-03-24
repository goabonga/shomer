## feat(session): browser session management service

## Summary

Complete session management service: create, validate, renew, delete, list by user. Session token encrypted with AES-256-GCM stored in HttpOnly cookie.

## Changes

- [ ] Session creation with AES-256-GCM encrypted token
- [ ] Session validation and lookup by token
- [ ] Session renewal (sliding expiration)
- [ ] Session deletion (single session)
- [ ] Delete all sessions for a user
- [ ] List active sessions by user
- [ ] Unit tests

## Dependencies

- #1 - AES-256-GCM encryption
- #6 - Session model

## Related Issue

Closes #20

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



# feat(session): browser session management service

## Description

Complete session management service: create, validate, renew, delete, list by user. Session token encrypted with AES-256-GCM stored in HttpOnly cookie.

## Objective

Provide the session layer for all browser-based authentication flows.

## Tasks

- [ ] Session creation with AES-256-GCM encrypted token
- [ ] Session validation and lookup by token
- [ ] Session renewal (sliding expiration)
- [ ] Session deletion (single session)
- [ ] Delete all sessions for a user
- [ ] List active sessions by user
- [ ] Unit tests

## Dependencies

- #1 — AES-256-GCM encryption
- #6 — Session model

## Labels

`feature:session`, `type:service`, `size:L`

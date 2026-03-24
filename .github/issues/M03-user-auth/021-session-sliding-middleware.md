# feat(session): sliding session expiration middleware

## Description

FastAPI middleware for automatic session renewal on each request (sliding expiration). Updates last_activity and extends TTL.

## Objective

Keep active sessions alive transparently without requiring explicit refresh calls.

## Tasks

- [ ] Middleware implementation
- [ ] Update last_activity timestamp on each request
- [ ] Extend session TTL if within renewal window
- [ ] Skip for unauthenticated requests

## Dependencies

- #20 — session service

## Labels

`feature:session`, `type:infra`, `size:S`

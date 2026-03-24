## feat(oauth2): OAuth2 client management service

## Summary

CRUD service for OAuth2 clients: creation with client_id/secret generation, redirect_uri validation, client authentication per RFC 6749 §2.3 (Basic, POST body, none), secret rotation.

## Changes

- [ ] Client creation with random client_id and hashed client_secret (Argon2id)
- [ ] Client lookup by client_id
- [ ] `client_secret_basic` authentication (RFC 6749 §2.3.1 — HTTP Basic, MUST support)
- [ ] `client_secret_post` authentication (RFC 6749 §2.3.1 — POST body)
- [ ] `none` authentication (public clients — client_id only, no secret)
- [ ] `token_endpoint_auth_method` field on OAuth2Client model
- [ ] Redirect URI validation (exact match, no fragments, no wildcards)
- [ ] Secret rotation (generate new, invalidate old)
- [ ] Unit tests

## Dependencies

- #1 - Argon2id for secret hashing
- #27 - OAuth2Client model

## Related Issue

Closes #28

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present

# feat(models): OAuth2Client

## Description

OAuth2Client model with client_id, hashed client_secret, redirect_uris, allowed grant_types, response_types, scopes, type (confidential/public), and OIDC metadata (logo_uri, tos_uri, etc.).

## Objective

Define the client entity that all OAuth2 flows authenticate against.

## Tasks

- [ ] OAuth2Client model with all fields
- [ ] Client type enum (confidential, public)
- [ ] JSON columns for redirect_uris, grant_types, response_types, scopes
- [ ] OIDC metadata fields (logo_uri, tos_uri, policy_uri, contacts)
- [ ] Alembic migration

## Dependencies

- #3 — declarative base

## Labels

`rfc:6749`, `type:model`, `size:M`

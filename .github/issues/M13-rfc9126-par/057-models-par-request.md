# feat(models): PARRequest

## Description

PARRequest model storing request_uri (urn:ietf:params:oauth:request_uri:xxx), all authorization request parameters, client_id, and short expiration (60s default).

## Objective

Persist pushed authorization requests so they can be retrieved by /authorize via request_uri.

## Tasks

- [ ] PARRequest model with request_uri, client_id, parameters JSON, expires_at
- [ ] Unique constraint on request_uri
- [ ] Short default TTL (60 seconds)
- [ ] Alembic migration

## Dependencies

- #27 — OAuth2Client model

## Labels

`rfc:9126`, `type:model`, `size:S`

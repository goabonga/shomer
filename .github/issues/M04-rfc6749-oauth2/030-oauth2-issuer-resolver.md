# feat(oauth2): dynamic issuer resolver service

## Description

Service for resolving the issuer URL based on the current tenant. Provides dynamic base URL for tokens and OIDC discovery.

## Objective

Support multi-tenant issuer values so each tenant has its own issuer URL.

## Tasks

- [ ] Issuer resolution from tenant context
- [ ] Fallback to default issuer when no tenant
- [ ] Used by JWT creation, discovery, and token responses
- [ ] Unit tests

## Dependencies

- #2 — configuration

## Labels

`oidc:core`, `type:service`, `size:S`

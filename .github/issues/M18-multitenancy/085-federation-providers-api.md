# feat(federation): GET /federation/providers

## Description

Endpoint listing available identity providers for the current tenant. Used by the login UI to display social login buttons.

## Objective

Allow the frontend to discover which external login options are available.

## Tasks

- [ ] GET `/federation/providers` route
- [ ] Filter by current tenant
- [ ] Return provider name, type, logo, authorization URL
- [ ] Integration test

## Dependencies

- #84 — IdentityProvider model

## Labels

`feature:federation`, `type:route`, `layer:api`, `size:S`

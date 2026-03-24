# feat(middleware): CORS and secure cookie policy

## Description

CORS configuration with dynamic origins (per-tenant) and secure cookie policy (HttpOnly, Secure, SameSite=Lax).

## Objective

Ensure cross-origin requests and cookies are handled securely by default across all tenants.

## Tasks

- [ ] CORS middleware with configurable allowed origins
- [ ] Dynamic origin resolution per tenant
- [ ] Secure cookie defaults (HttpOnly, Secure, SameSite=Lax)
- [ ] Development mode with relaxed CORS for localhost

## Dependencies

- #2 — configuration

## Labels

`type:infra`, `rfc:6749`, `size:S`

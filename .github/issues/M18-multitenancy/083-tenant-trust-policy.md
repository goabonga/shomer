# feat(tenant): trust policy — TenantTrustedSource + service

## Description

Trust policy management: TenantTrustedSource model defining trusted email domains, IP ranges, and identity providers per tenant. Service for evaluating trust during registration and login.

## Objective

Allow tenants to restrict who can register or login based on configurable trust rules.

## Tasks

- [ ] TenantTrustedSource model (tenant_id, source_type, source_value, policy)
- [ ] Trust evaluation service
- [ ] Email domain trust check (e.g., only @acme.com can register)
- [ ] IP range trust check
- [ ] IdP trust check
- [ ] Unit tests

## Dependencies

- #79 — Tenant model

## Labels

`feature:trust`, `feature:tenant`, `size:M`

# feat(models): Session with CSRF and multi-tenancy

## Description

Session model with CSRF token, multi-tenancy support (tenant_id), user-agent, IP address, last activity timestamp, and sliding expiration.

## Objective

Provide a session storage model that supports browser sessions across multiple tenants.

## Tasks

- [ ] Session model (token_hash, csrf_token, user_id, tenant_id, user_agent, ip_address, last_activity, expires_at)
- [ ] Indexes on user_id and tenant_id
- [ ] Alembic migration

## Dependencies

- #4 — User model

## Labels

`feature:session`, `type:model`, `size:S`

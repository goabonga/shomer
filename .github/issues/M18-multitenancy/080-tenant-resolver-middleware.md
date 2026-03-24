# feat(tenant): tenant resolution middleware (subdomain, path, custom domain)

## Description

Middleware that resolves the current tenant from the request: subdomain matching, path prefix, or custom domain lookup. Sets tenant context for the entire request lifecycle.

## Objective

Enable transparent tenant resolution so all downstream code operates in the correct tenant context.

## Tasks

- [ ] Subdomain-based resolution (e.g., acme.shomer.io)
- [ ] Path-based resolution (e.g., /t/acme/...)
- [ ] Custom domain resolution (e.g., auth.acme.com)
- [ ] Set tenant in request state
- [ ] Fallback to default tenant
- [ ] Unit tests

## Dependencies

- #79 — Tenant model

## Labels

`feature:tenant`, `type:infra`, `size:L`

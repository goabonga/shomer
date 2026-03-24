## feat(tenant): tenant resolution middleware (subdomain, path, custom domain)

## Summary

Middleware that resolves the current tenant from the request: subdomain matching, path prefix, or custom domain lookup. Sets tenant context for the entire request lifecycle.

## Changes

- [ ] Subdomain-based resolution (e.g., acme.shomer.io)
- [ ] Path-based resolution (e.g., /t/acme/...)
- [ ] Custom domain resolution (e.g., auth.acme.com)
- [ ] Set tenant in request state
- [ ] Fallback to default tenant
- [ ] Unit tests

## Dependencies

- #79 - Tenant model

## Related Issue

Closes #80

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



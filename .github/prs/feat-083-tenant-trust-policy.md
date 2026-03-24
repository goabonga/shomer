## feat(tenant): trust policy - TenantTrustedSource + service

## Summary

Trust policy management: TenantTrustedSource model defining trusted email domains, IP ranges, and identity providers per tenant. Service for evaluating trust during registration and login.

## Changes

- [ ] TenantTrustedSource model (tenant_id, source_type, source_value, policy)
- [ ] Trust evaluation service
- [ ] Email domain trust check (e.g., only @acme.com can register)
- [ ] IP range trust check
- [ ] IdP trust check
- [ ] Unit tests

## Dependencies

- #79 - Tenant model

## Related Issue

Closes #83

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



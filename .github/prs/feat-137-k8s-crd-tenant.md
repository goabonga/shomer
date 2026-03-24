## feat(k8s): CRD ShomerTenant

## Summary

Custom Resource Definition for managing tenants via Kubernetes manifests. Supports tenant CRUD, member management, branding, and custom domains.

## Changes

- [ ] CRD `ShomerTenant` (apiVersion: shomer.io/v1alpha1)
- [ ] Spec: slug, name, settings, members[], branding{}, customDomains[]
- [ ] Status: tenantId, ready, domainStatuses[], conditions, lastSyncedAt
- [ ] Controller: create/update/delete via admin API
- [ ] Member management (add/remove based on spec diff)
- [ ] Domain status tracking (pending_dns, pending_ssl, active)
- [ ] Finalizer for cleanup on deletion
- [ ] Unit + envtest tests
- [ ] CRD documentation with examples

## Dependencies

- #134 - operator scaffold
- #93 - admin tenants API

## Related Issue

Closes #137

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



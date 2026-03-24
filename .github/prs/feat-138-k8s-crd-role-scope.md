## feat(k8s): CRDs ShomerRole, ShomerScope

## Summary

Custom Resource Definitions for managing RBAC roles and scopes via Kubernetes manifests. Includes scope-to-role assignment.

## Changes

- [ ] CRD `ShomerScope` (apiVersion: shomer.io/v1alpha1) - spec: name, description
- [ ] CRD `ShomerRole` (apiVersion: shomer.io/v1alpha1) - spec: name, description, scopeRefs[]
- [ ] Status: ready, conditions, lastSyncedAt
- [ ] Controllers: create/update/delete via admin API
- [ ] Scope assignment reconciliation (add/remove based on scopeRefs diff)
- [ ] Finalizers for cleanup
- [ ] Unit + envtest tests
- [ ] CRD documentation with examples

## Dependencies

- #134 - operator scaffold
- #92 - admin roles/scopes API

## Related Issue

Closes #138

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



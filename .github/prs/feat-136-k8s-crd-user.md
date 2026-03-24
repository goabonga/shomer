## feat(k8s): CRD ShomerUser

## Summary

Custom Resource Definition for managing users via Kubernetes manifests. Supports user creation, activation, role assignment, and deletion.

## Changes

- [ ] CRD `ShomerUser` (apiVersion: shomer.io/v1alpha1)
- [ ] Spec: email, username, passwordSecretRef, isActive, roles[], verified
- [ ] Status: userId, ready, conditions, lastSyncedAt
- [ ] Controller: create/update/delete via admin API
- [ ] Password from Kubernetes Secret reference
- [ ] Finalizer for cleanup on deletion
- [ ] Unit + envtest tests
- [ ] CRD documentation with examples

## Dependencies

- #134 - operator scaffold
- #88 - admin users API

## Related Issue

Closes #136

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



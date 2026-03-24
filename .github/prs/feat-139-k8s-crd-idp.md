## feat(k8s): CRD ShomerIdentityProvider

## Summary

Custom Resource Definition for managing identity provider configurations per tenant via Kubernetes manifests.

## Changes

- [ ] CRD `ShomerIdentityProvider` (apiVersion: shomer.io/v1alpha1)
- [ ] Spec: tenantRef, name, type (google/github/microsoft/oidc), clientId, clientSecretRef, authorizationUrl, tokenUrl, userinfoUrl, claimMapping
- [ ] Status: ready, conditions, lastSyncedAt
- [ ] Controller: create/update/delete via admin API
- [ ] Client secret from Kubernetes Secret reference
- [ ] Finalizer for cleanup on deletion
- [ ] Unit + envtest tests
- [ ] CRD documentation with examples

## Dependencies

- #134 - operator scaffold
- #93 - admin tenants API (IdP sub-resources)

## Related Issue

Closes #139

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



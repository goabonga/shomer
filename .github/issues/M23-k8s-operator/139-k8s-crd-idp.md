# feat(k8s): CRD ShomerIdentityProvider

## Description

Custom Resource Definition for managing identity provider configurations per tenant via Kubernetes manifests.

## Objective

Allow federation/social login setup via `kubectl apply`.

## Tasks

- [ ] CRD `ShomerIdentityProvider` (apiVersion: shomer.io/v1alpha1)
- [ ] Spec: tenantRef, name, type (google/github/microsoft/oidc), clientId, clientSecretRef, authorizationUrl, tokenUrl, userinfoUrl, claimMapping
- [ ] Status: ready, conditions, lastSyncedAt
- [ ] Controller: create/update/delete via admin API
- [ ] Client secret from Kubernetes Secret reference
- [ ] Finalizer for cleanup on deletion
- [ ] Unit + envtest tests
- [ ] CRD documentation with examples

## Dependencies

- #134 — operator scaffold
- #93 — admin tenants API (IdP sub-resources)

## Labels

`feature:admin`, `feature:federation`, `size:M`

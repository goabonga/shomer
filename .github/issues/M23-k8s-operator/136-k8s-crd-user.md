# feat(k8s): CRD ShomerUser

## Description

Custom Resource Definition for managing users via Kubernetes manifests. Supports user creation, activation, role assignment, and deletion.

## Objective

Allow user provisioning via `kubectl apply`, useful for bootstrapping and GitOps workflows.

## Tasks

- [ ] CRD `ShomerUser` (apiVersion: shomer.io/v1alpha1)
- [ ] Spec: email, username, passwordSecretRef, isActive, roles[], verified
- [ ] Status: userId, ready, conditions, lastSyncedAt
- [ ] Controller: create/update/delete via admin API
- [ ] Password from Kubernetes Secret reference
- [ ] Finalizer for cleanup on deletion
- [ ] Unit + envtest tests
- [ ] CRD documentation with examples

## Dependencies

- #134 — operator scaffold
- #88 — admin users API

## Labels

`feature:admin`, `feature:auth`, `size:M`

# feat(k8s): CRDs ShomerRole, ShomerScope

## Description

Custom Resource Definitions for managing RBAC roles and scopes via Kubernetes manifests. Includes scope-to-role assignment.

## Objective

Allow RBAC configuration as Kubernetes resources for GitOps workflows.

## Tasks

- [ ] CRD `ShomerScope` (apiVersion: shomer.io/v1alpha1) — spec: name, description
- [ ] CRD `ShomerRole` (apiVersion: shomer.io/v1alpha1) — spec: name, description, scopeRefs[]
- [ ] Status: ready, conditions, lastSyncedAt
- [ ] Controllers: create/update/delete via admin API
- [ ] Scope assignment reconciliation (add/remove based on scopeRefs diff)
- [ ] Finalizers for cleanup
- [ ] Unit + envtest tests
- [ ] CRD documentation with examples

## Dependencies

- #134 — operator scaffold
- #92 — admin roles/scopes API

## Labels

`feature:admin`, `feature:rbac`, `size:L`

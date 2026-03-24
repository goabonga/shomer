# feat(k8s): CRD ShomerTenant

## Description

Custom Resource Definition for managing tenants via Kubernetes manifests. Supports tenant CRUD, member management, branding, and custom domains.

## Objective

Allow multi-tenant provisioning via `kubectl apply` for GitOps-driven infrastructure.

## Tasks

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

- #134 — operator scaffold
- #93 — admin tenants API

## Labels

`feature:admin`, `feature:tenant`, `size:XL`

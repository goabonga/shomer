# feat(k8s): CRD ShomerOAuth2Client

## Description

Custom Resource Definition for managing OAuth2 clients via Kubernetes manifests. The operator reconciles the desired state with the Shomer API.

## Objective

Allow OAuth2 client registration and management via `kubectl apply`.

## Tasks

- [ ] CRD `ShomerOAuth2Client` (apiVersion: shomer.io/v1alpha1)
- [ ] Spec: name, clientType, redirectUris, grantTypes, responseTypes, scopes, logoUri, tosUri
- [ ] Status: clientId, ready, conditions, lastSyncedAt
- [ ] Controller: create/update/delete via admin API
- [ ] Client secret stored in a Kubernetes Secret (auto-created, referenced in status)
- [ ] Secret rotation via annotation trigger
- [ ] Finalizer for cleanup on deletion
- [ ] Unit + envtest tests
- [ ] CRD documentation with examples

## Dependencies

- #134 — operator scaffold
- #89 — admin clients API

## Labels

`feature:admin`, `feature:oauth2`, `rfc:6749`, `size:L`

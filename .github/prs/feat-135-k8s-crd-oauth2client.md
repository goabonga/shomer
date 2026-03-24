## feat(k8s): CRD ShomerOAuth2Client

## Summary

Custom Resource Definition for managing OAuth2 clients via Kubernetes manifests. The operator reconciles the desired state with the Shomer API.

## Changes

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

- #134 - operator scaffold
- #89 - admin clients API

## Related Issue

Closes #135

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present



## feat(k8s): Kubernetes operator scaffold with controller-runtime

## Summary

Scaffold the Shomer Kubernetes operator using kubebuilder and controller-runtime (Go). Set up the project structure, CRD generation, RBAC, leader election, and Helm chart for deploying the operator.

## Changes

- [ ] kubebuilder project initialization
- [ ] Operator configuration: Shomer API URL, authentication (PAT secret reference or ServiceAccount-based)
- [ ] HTTP client for Shomer admin API with retry and error handling
- [ ] Leader election for HA deployments
- [ ] RBAC (ClusterRole, ServiceAccount) for the operator
- [ ] Helm chart for operator deployment
- [ ] CI: build, lint, test, Docker image, Helm publish
- [ ] Integration test framework (envtest)

## Dependencies

None - this is the operator foundation.

## Related Issue

Closes #134

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present


